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

(import ctypes
        pathlib
        clang.cindex
        dataclasses [dataclass])

(defclass [(dataclass :frozen True)] CInterface []
  #^ dict types
  #^ dict symbols
  #^ dict enum-consts)

(defn remove-qualifiers-and-specifiers [name]
  (setv qualifiers-and-specifiers ["const"
                                   "volatile"
                                   "enum"
                                   "struct"
                                   "union"
                                   "restrict"])
  (setv words (.split name))
  (setv filtered-words (filter (fn [x] (not (in x qualifiers-and-specifiers))) words))
  (return (.join " " filtered-words)))

(defn unique-type-name [#^(. clang cindex Type) clang-type]
  "Generate the name of the ctype type"
  (if (.is_anonymous (.get_declaration clang-type))
      (hex (hash (. (.get_canonical clang-type) spelling)))
      (remove-qualifiers-and-specifiers (. clang-type spelling))))
