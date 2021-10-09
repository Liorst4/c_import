(import subprocess
        ctypes
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


(defn load ^(. ctypes CDLL) [^Path library
                             ^(of Sequence Path) headers
                             &optional
                             [cpp-command None]
                             [cpp-flags None]]
  (setv dll (.CDLL ctypes library)
        interface (with [combined-header (NamedTemporaryFile :mode "w"
                                                             :encoding "utf-8"
                                                             :suffix ".h"
                                                             :delete False)]
                    (do
                      (->> (preprocess-headers headers
                                               cpp-command
                                               cpp-flags)
                           (.write combined-header))
                      (.flush combined-header)
                      (parse-header (. combined-header name)))))
  (setv (. dll types) (. interface types))
  (for [[key value] (.items (. interface symbols))
        :if (hasattr dll key)]
    (->> (getattr dll key)
         ;; TODO: Applying POINTER onto a CFUCNTYPE is necessary?
         ((.POINTER ctypes value))
         (setattr dll key)))
  (for [[key value] (.items (. interface enum-consts))]
    (setattr dll key value))
  dll)
