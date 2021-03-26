(import subprocess
        [tempfile [NamedTemporaryFile]]
        [pathlib [Path]]
        [typing [Sequence]])

(defn preprocess-headers ^str [^(of Sequence Path) headers
                               ^(of Sequence str) cpp-flags
                               ^str cpp-command]
  (with [include-all-file (NamedTemporaryFile :mode "w"
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
