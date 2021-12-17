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

(require [hy.contrib.walk [let]])

(import ctypes
        pathlib
        clang.cindex
        [dataclasses [dataclass]]
        [typing [Dict Union]])

(with-decorator (dataclass :frozen True)
  (defclass CInterface []
    (^(of Dict str type) types)
    (^(of Dict str object) symbols)
    (^(of Dict str int) enum-consts)))

(defn remove-qualifiers-and-specifiers [name]
  (->> name
       (.split)
       (filter (fn [x] (not (in x ["const"
                                   "volatile"
                                   "enum"
                                   "struct"
                                   "union"
                                   "restrict"]))))
       (.join " ")))

(defn ^str unique-type-name [^(. clang cindex Type) clang-type]
  "Generate the name of the ctype type"
  (if (-> clang-type
          .get_declaration
          .is_anonymous)
      (-> clang-type
          (.get_canonical)
          (. spelling)
          (hash)
          (hex))
      (-> (. clang-type spelling)
          remove-qualifiers-and-specifiers)))

(defn get-type-or-create-variant [^CInterface scope
                                  ^(. clang cindex Type) clang-type]
  ;; TODO: Handle anonymous and opaque types
  (assert (. clang-type spelling))
  (match clang-type.kind
         clang.cindex.TypeKind.BOOL ctypes.c_bool
         (| clang.cindex.TypeKind.CHAR_U clang.cindex.TypeKind.UCHAR) ctypes.c_ubyte
         clang.cindex.TypeKind.USHORT ctypes.c_ushort
         clang.cindex.TypeKind.UINT ctypes.c_uint
         clang.cindex.TypeKind.ULONG ctypes.c_ulong
         clang.cindex.TypeKind.ULONGLONG ctypes.c_ulonglong
         (| clang.cindex.TypeKind.CHAR_S clang.cindex.TypeKind.SCHAR) ctypes.c_char
         clang.cindex.TypeKind.WCHAR ctypes.c_wchar
         clang.cindex.TypeKind.SHORT ctypes.c_short
         (| clang.cindex.TypeKind.INT clang.cindex.TypeKind.ENUM) ctypes.c_int
         clang.cindex.TypeKind.LONG ctypes.c_long
         clang.cindex.TypeKind.LONGLONG ctypes.c_longlong
         clang.cindex.TypeKind.FLOAT ctypes.c_float
         clang.cindex.TypeKind.DOUBLE ctypes.c_double
         clang.cindex.TypeKind.LONGDOUBLE ctypes.c_longdouble
         clang.cindex.TypeKind.VOID None
         clang.cindex.TypeKind.INVALID (raise ValueError)

         clang.cindex.TypeKind.POINTER (->> (.get_pointee clang-type)
                                            (get-type-or-create-variant scope)
                                            (.POINTER ctypes))

         clang.cindex.TypeKind.CONSTANTARRAY (-> (get-type-or-create-variant scope
                                                                             clang-type.element_type)
                                                 (ctypes.ARRAY clang-type.element_count))

         clang.cindex.TypeKind.FUNCTIONPROTO (do (assert (not (.is_function_variadic clang-type)))
                                                 (.CFUNCTYPE ctypes
                                                             (->> clang-type
                                                                  .get_result
                                                                  (get-type-or-create-variant scope))
                                                             (->> clang-type
                                                                  .argument_types
                                                                  (map (fn [x] (get-type-or-create-variant scope x)))
                                                                  unpack-iterable)))

         clang.cindex.TypeKind.INCOMPLETEARRAY (->> (. clang-type element_type)
                                                    (get-type-or-create-variant scope)
                                                    (.POINTER ctypes))

         clang.cindex.TypeKind.TYPEDEF (->> (.get_canonical clang-type)
                                            (get-type-or-create-variant scope))



         clang.cindex.TypeKind.RECORD (let [type-id (unique-type-name clang-type)]
                                        (unless (in type-id (. scope types))
                                          (handle-struct-deceleration scope
                                                                      (.get_declaration clang-type)))
                                        (get (. scope types) type-id))

         clang.cindex.TypeKind.ELABORATED (get (. scope types)
                                               (unique-type-name clang-type))

         unkown (raise (NotImplementedError unkown))))

(defn handle-typedef-deceleration [^CInterface scope ^(. clang cindex Cursor) cursor]
  (assert (= (. cursor kind)
             (. clang cindex CursorKind TYPEDEF_DECL)))
  (assoc (. scope types)
         (. cursor spelling)
         (get-type-or-create-variant scope
                                     (. cursor underlying_typedef_type))))

(defn handle-type-declaration-body [^CInterface scope
                                    ^(. clang cindex Cursor) cursor
                                    ^type empty-ctype]
  "Handle variables, structs, unions, packed attrs, etc... in a ctype."

  (setv fields-to-add []
        pack-value None
        anon-types-to-add [])

  (for [child (.get_children cursor)]
    (match child.kind
           clang.cindex.CursorKind.FIELD_DECL (.append fields-to-add
                                                       (let [field [(. child spelling)
                                                                    (get-type-or-create-variant scope
                                                                                                child.type)]]
                                                         (when (.is_bitfield child)
                                                           (.append field
                                                                    (.get_bitfield_width child)))

                                                         ;; If its bounded to a field, than its not suppose to be in _anonymous_
                                                         (let [field-type-name (. (get field 1) __name__)]
                                                           (when (in field-type-name anon-types-to-add)
                                                             (.remove anon-types-to-add field-type-name)))

                                                         (tuple field)))

           clang.cindex.CursorKind.PACKED_ATTR (setv pack-value 1)

           (| clang.cindex.CursorKind.STRUCT_DECL
              clang.cindex.CursorKind.UNION_DECL) :as kind (let [handler (match kind
                                                                                clang.cindex.CursorKind.STRUCT_DECL handle-struct-deceleration
                                                                                clang.cindex.CursorKind.UNION_DECL handle-union-deceleration)
                                                                 nested-ctype-name (unique-type-name child.type)]
                                                             (unless (in nested-ctype-name scope.types)
                                                               (let [nested-ctype (handler scope child)]
                                                                 (.append anon-types-to-add nested-ctype-name)
                                                                 (.append fields-to-add (tuple [nested-ctype-name
                                                                                                nested-ctype])))))


           unkwon (raise (NotImplementedError child.kind))))

  (when pack-value
    (setv (. empty-ctype _pack_) pack-value))
  (when anon-types-to-add
    (do (for [t (map (fn [x] (get (. scope types ) x))
                     anon-types-to-add)]
              (unless (hasattr t "_fields_")
                (setattr t "_fields_" [])))
      (setv (. empty-ctype _anonymous_) anon-types-to-add)))
  (when fields-to-add
    (setv (. empty-ctype _fields_) fields-to-add)))

(defn add-type-with-feilds [expected-cursor-kind
                            ctypes-type
                            ^CInterface scope
                            ^(. clang cindex Cursor) cursor]
  "Add (or expand in the case of a forward decleration) a ctype with fields to a scope"
  (assert (= (. cursor kind) expected-cursor-kind))
  (setv type-name (unique-type-name (. cursor type))
        ctype (if (in type-name (. scope types))

                  ;; Get a forward decleration reference
                  ;; to expand.
                  ;; TODO: Verifiy its a forward decleration
                  (get (. scope types) type-name)

                  ;; Create a new ctypes class
                  (type type-name
                        (tuple [ctypes-type])
                        (dict))))

  (assert (not (in " " type-name)))
  (assoc (. scope types) type-name ctype) ;; Add refrence to table

  ;; Create body
  (handle-type-declaration-body scope cursor ctype)
  ctype)

(defn handle-struct-deceleration [^CInterface scope ^(. clang cindex Cursor) cursor]
  (add-type-with-feilds (. clang cindex CursorKind STRUCT_DECL)
                        (. ctypes Structure)
                        scope
                        cursor))

(defn handle-union-deceleration [^CInterface scope ^(. clang cindex Cursor) cursor]
  (add-type-with-feilds (. clang cindex CursorKind UNION_DECL)
                        (. ctypes Union)
                        scope
                        cursor))

(defn handle-enum-deceleration [^CInterface scope ^(. clang cindex Cursor) cursor]
  (assert (= (. cursor kind)
             (. clang cindex CursorKind ENUM_DECL)))
  (setv enum-name (unique-type-name (. cursor type)))
  (assoc (. scope types)
         enum-name
         (. ctypes c_int))
  (for [c (.get_children cursor)]
    (do (assert (= (. clang
                      cindex
                      CursorKind
                      ENUM_CONSTANT_DECL)
                   (. c kind)))
        (assoc (. scope enum-consts)
               (. c spelling)
               (. c enum_value)))))

(defn handle-var-deceleration [^CInterface scope ^(. clang cindex Cursor) cursor]
  (assert (= (. cursor kind)
             (. clang cindex CursorKind VAR_DECL)))
  (setv var-type (get-type-or-create-variant scope (. cursor type)))
  (assoc (. scope symbols) (. cursor spelling) var-type))

(defn handle-function-deceleration [^CInterface scope ^(. clang cindex Cursor) cursor]
  ;; TODO: Handle stdcall
  (assert (= (. cursor kind)
             (. clang cindex CursorKind FUNCTION_DECL)))
  (setv function (.CFUNCTYPE ctypes
                             (->> (. cursor result_type)
                                  (get-type-or-create-variant scope))
                             (->> cursor
                                  .get_arguments
                                  (map (fn [x] (->> (. x type)
                                                    (get-type-or-create-variant scope))))
                                  unpack-iterable)))
  (assoc (. scope symbols) (. cursor spelling) function))

(defn handle-deceleration [^CInterface scope ^(. clang cindex Cursor) cursor]
  (assert (.is_declaration (. cursor kind)))
  (let [handler (match cursor.kind
                       clang.cindex.CursorKind.TYPEDEF_DECL handle-typedef-deceleration
                       clang.cindex.CursorKind.STRUCT_DECL handle-struct-deceleration
                       clang.cindex.CursorKind.UNION_DECL handle-union-deceleration
                       clang.cindex.CursorKind.ENUM_DECL handle-enum-deceleration
                       clang.cindex.CursorKind.VAR_DECL handle-var-deceleration
                       clang.cindex.CursorKind.FUNCTION_DECL handle-function-deceleration
                       unkown (raise (NotImplementedError unkwon)))]
    (handler scope cursor)))

(defn handle-translation-unit [^CInterface scope
                               ^(. clang cindex Cursor) cursor]
  (assert (= (. cursor kind)
             (. clang cindex CursorKind TRANSLATION_UNIT)))
  (for [child (.get_children cursor)]
      (handle-deceleration scope child)))

(defn ^CInterface parse-header [^(. pathlib Path) header]
  "Create a CInterface instance from a given header file."
  (setv scope (CInterface :types (dict)
                          :symbols (dict)
                          :enum-consts (dict)))
  (handle-translation-unit scope
                           (-> (clang.cindex.Index.create)
                               (.parse header)
                               (. cursor)))
  (assert (->> (in "" (.keys (. scope types)))
               not))
  scope)
