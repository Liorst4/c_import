;; Copyright (C) 2022  Lior Stern
;;
;; This file is part of c_import.
;;
;; c_import is free software: you can redistribute it and/or modify
;; it under the terms of the GNU Lesser General Public License as published by
;; the Free Software Foundation, either version 3 of the License, or
;; (at your option) any later version.
;;
;; c_import is distributed in the hope that it will be useful,
;; but WITHOUT ANY WARRANTY; without even the implied warranty of
;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;; GNU General Public License for more details.
;;
;; You should have received a copy of the GNU Lesser General Public License
;; along with c_import.  If not, see <https://www.gnu.org/licenses/>.
;;
;; SPDX-License-Identifier: LGPL-3.0-or-later

;; (require [hy.contrib.walk [let]])

(import subprocess
        ctypes
        _ctypes
        os
        itertools [chain]
        tempfile [NamedTemporaryFile]
        pathlib [Path]
        typing [Sequence Optional]
        c_import.header_parser [parse_header CInterface])

(defn preprocess-headers [headers cpp-command cpp-flags]

  ;; Common mistake
  (assert (not (isinstance headers str))
          "headrs should be a list of paths, not a single path!")

  (if (not cpp-command)
      (setv cpp-command (.get (. os environ) "CPP" "cpp"))
      (do ))
  (if (not cpp-flags)
      (setv cpp-flags (.get (. os environ) "CPPFLAGS" []))
      (do ))
  (with [include-all-file (NamedTemporaryFile :mode "w"
                                              :suffix ".h"
                                              :encoding "utf-8")]
    (do
      (for [header-file headers]
        (.write include-all-file (.format "#include <{}>\n" header-file)))
      (.flush include-all-file)
      (. (.run subprocess
                (list (chain [cpp-command (. include-all-file name)]
                             cpp-flags))
                :check True
                :encoding "utf-8"
                :stdout (. subprocess PIPE))
         stdout))))

;; TODO: Better name
(defclass CDLLX [(. ctypes CDLL)]
  (defn __init__ [self
                  library
                  headers
                  [cpp-command None]
                  [cpp-flags None]]
    ((. (super) __init__) library)
    (setv self._interface (with [combined-header (NamedTemporaryFile :mode "w"
                                                                     :encoding "utf-8"
                                                                     :suffix ".h")]
                            (do (.write combined-header (preprocess-headers headers
                                                                            cpp-command
                                                                            cpp-flags))
                                (.flush combined-header)
                                (parse-header (. combined-header name))))))

  (defn __getitem__ [self item]
    (cond (in item self._interface.symbols) (let [ctype (get self._interface.symbols item)]
                                              (if (issubclass ctype _ctypes.CFuncPtr)
                                                  (ctype (tuple [item self]))
                                                  (.in_dll ctype self item)))
          (in item self._interface.enum-consts) (get self._interface.enum-consts item)
          (in item self._interface.types) (get self._interface.types item)
          True (raise KeyError))))
