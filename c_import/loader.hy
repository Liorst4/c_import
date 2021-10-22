(import subprocess
        ctypes
        _ctypes
        os
        [tempfile [NamedTemporaryFile]]
        [pathlib [Path]]
        [typing [Sequence Optional]]
        [c_import.header_parser [parse_header CInterface]])

(defn preprocess-headers ^str [^(of Sequence Path) headers
                               ^(of Optional str) cpp-command
                               ^(of Sequence str) cpp-flags]
  (unless cpp-command
    (setv cpp-command (.get (. os environ) "CPP" "cpp")))
  (unless cpp-flags
    (setv cpp-flags (.get (. os environ) "CPPFLAGS" [])))
  (with [include-all-file (NamedTemporaryFile :mode "w"
                                              :suffix ".h"
                                              :encoding "utf-8")]
    (do
      (for [header-file headers]
        (.write include-all-file (.format "#include <{}>\n" header-file)))
      (.flush include-all-file)
      (setv cpp-result (.run subprocess
                             (list (chain [cpp-command (. include-all-file name)] cpp-flags))
                             :check True
                             :encoding "utf-8"
                             :stdout (. subprocess PIPE)))
      (. cpp-result stdout))))

;; TODO: Better name
(defclass CDLLX [(. ctypes CDLL)]
  (defn __init__ [self
                  ^Path library
                  ^(of Sequence Path) headers
                  &optional
                  [cpp-command None]
                  [cpp-flags None]]
    ((. (super) __init__) library)
    (setv self._interface (with [combined-header (NamedTemporaryFile :mode "w"
                                                                     :encoding "utf-8"
                                                                     :suffix ".h")]
                            (do (->> (preprocess-headers headers
                                                         cpp-command
                                                         cpp-flags)
                                     (.write combined-header))
                                (.flush combined-header)
                                (parse-header (. combined-header name))))))

  (defn __getitem__ [self item]
    (if (in item self._interface.symbols)
        (do (setv symbol-address (_ctypes.dlsym self._handle item)
                  ctype (get self._interface.symbols item)
                  ref-constructor (cond [(issubclass ctype _ctypes.CFuncPtr) ctype]
                                        [(issubclass ctype _ctypes._Pointer) (fn [x] ((. ctype from_address) x))]
                                        [True (fn [x] ((. (.POINTER ctypes ctype) from_address) x))]))
            (ref-constructor symbol-address))
        ((. (super) __getitem__) item))))

;; TODO: Delete?
(setv load CDLLX)
