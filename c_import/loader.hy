(import subprocess
        ctypes
        [tempfile [NamedTemporaryFile]]
        [pathlib [Path]]
        [typing [Sequence]]
        [c_import.header_parser [parse_header CInterface]])

(defn preprocess-headers ^str [^(of Sequence Path) headers
                               ^(of Sequence str) cpp-flags
                               ^str cpp-command]
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
                             [cpp-command "cpp"]
                             [cpp-flags []]]
  (setv dll (.CDLL ctypes library)
        interface (with [combined-header (NamedTemporaryFile :mode "w"
                                                             :encoding "utf-8"
                                                             :suffix ".h"
                                                             :delete False)]
                    (do
                      (->> (preprocess-headers headers cpp-flags cpp-command)
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
  dll)
