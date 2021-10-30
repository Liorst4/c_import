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

  ;; Common mistake
  (assert (not (isinstance headers str))
          "headrs should be a list of paths, not a single path!")

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
      (-> (.run subprocess
                (list (chain [cpp-command (. include-all-file name)]
                             cpp-flags))
                :check True
                :encoding "utf-8"
                :stdout (. subprocess PIPE))
          (. stdout)))))

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
    (cond [(in item self._interface.symbols)
           (do (setv ctype (get self._interface.symbols item))
               (if (issubclass ctype _ctypes.CFuncPtr)
                   (ctype (tuple [item self]))
                   (.in_dll ctype self item)))]
          [(in item self._interface.enum-consts)
           (get self._interface.enum-consts item)]
          [(in item self._interface.types)
           (get self._interface.types item)]
          [True (raise KeyError)])))


;; TODO: Delete?
(setv load CDLLX)
