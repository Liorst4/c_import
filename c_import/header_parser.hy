(import ctypes
        pathlib
        enum
        [collections [defaultdict]]
        [typing [Dict Callable Tuple NamedTuple Union]])

(import clang.cindex)

(setv VoidType (type None)
      OptionalPointerWrapper (of Union (of Callable [int] object)
                                 VoidType)
      TypeTable (of Dict str (of Union
                                 OptionalPointerWrapper
                                 (. enum IntEnum)))
      SymbolTable (of Dict str OptionalPointerWrapper))

(defclass __unknown_type [(. ctypes c_int)]
  (setv _fields_ []))

(defclass CInterface [NamedTuple]
  (setv ^TypeTable types (dict)
        ^SymbolTable symbols (dict)))

(defn get-type-or-create-variant ^OptionalPointerWrapper [^CInterface scope
                                                          ^(. clang cindex Type) clang-type
                                                          &optional [keep-enum False]]
  ;; TODO: Handle anonymous and opaque types
  (assert (. clang-type spelling))
  ;; TODO: Use macro for kind switch?
  (cond [(= (. clang-type kind) (. clang cindex TypeKind POINTER))
         (->> (.get_pointee clang-type)
              (get-type-or-create-variant scope)
              (.POINTER ctypes))]
        [(= (. clang-type kind) (. clang cindex TypeKind BOOL))
         (. ctypes c_bool)]
        [(= (. clang-type kind) (. clang cindex TypeKind CHAR_U))
         (. ctypes c_ubyte)]
        [(= (. clang-type kind) (. clang cindex TypeKind UCHAR))
         (. ctypes c_ubyte)]
        ;; TODO: CHAR16
        ;; TODO: CHAR32
        [(= (. clang-type kind) (. clang cindex TypeKind USHORT))
         (. ctypes c_ushort)]
        [(= (. clang-type kind) (. clang cindex TypeKind UINT))
         (. ctypes c_uint)]
        [(= (. clang-type kind) (. clang cindex TypeKind ULONG))
         (. ctypes c_ulong)]
        [(= (. clang-type kind) (. clang cindex TypeKind ULONGLONG))
         (. ctypes c_ulonglong)]
        ;; TODO: UINT128
        [(= (. clang-type kind) (. clang cindex TypeKind CHAR_S))
         (. ctypes c_char)]
        [(= (. clang-type kind) (. clang cindex TypeKind SCHAR))
         (. ctypes c_char)]
        [(= (. clang-type kind) (. clang cindex TypeKind WCHAR))
         (. ctypes c_wchar)]
        [(= (. clang-type kind) (. clang cindex TypeKind SHORT))
         (. ctypes c_short)]
        [(= (. clang-type kind) (. clang cindex TypeKind INT))
         (. ctypes c_int)]
        [(= (. clang-type kind) (. clang cindex TypeKind LONG))
         (. ctypes c_long)]
        [(= (. clang-type kind) (. clang cindex TypeKind LONGLONG))
         (. ctypes c_longlong)]
        ;; TODO: INT128
        [(= (. clang-type kind) (. clang cindex TypeKind FLOAT))
         (. ctypes c_float)]
        [(= (. clang-type kind) (. clang cindex TypeKind DOUBLE))
         (. ctypes c_double)]
        [(= (. clang-type kind) (. clang cindex TypeKind LONGDOUBLE))
         (. ctypes c_longdouble)]
        ;; TODO: FLOAT128
        ;; TODO: COMPLEX

        [(= (. clang-type kind) (. clang cindex TypeKind CONSTANTARRAY))
         ((. ctypes ARRAY) (get-type-or-create-variant scope (. clang-type element_type)) (. clang-type element_count))]

        [(= (. clang-type kind) (. clang cindex TypeKind FUNCTIONPROTO))
         ;; TODO: Handle `...`
         (.CFUNCTYPE ctypes
                     (->> clang-type
                          .get_result
                          (get-type-or-create-variant scope))
                     (->> clang-type
                          .argument_types
                          (map (fn [x] (get-type-or-create-variant scope x)))
                          unpack-iterable))]

        [(= (. clang-type kind) (. clang cindex TypeKind VOID)) None]

        [(= (. clang-type kind) (. clang
                                   cindex
                                   TypeKind
                                   INCOMPLETEARRAY)) (->> (. clang-type element_type)
                                                          (get-type-or-create-variant scope)
                                                          (.POINTER ctypes))]

        ;; TODO: TYPEDEF
        ;; TODO: RECORD

        [True (do
                (setv type-id (->> (. clang-type spelling)
                                   (.split)
                                   (filter (fn [x] (not (in x ["const"
                                                               "volatile"
                                                               "enum"
                                                               "struct"
                                                               "union"]))))
                                   (.join " "))
                      existing-type (get (. scope types) type-id))
                (if (and existing-type
                         (not keep-enum)
                         (issubclass existing-type (. enum IntEnum)))
                    (. ctypes c_int)
                    existing-type))]))

(defn add-typedef [^CInterface scope ^(. clang cindex Cursor) cursor]
  (assoc (. scope types)
         (. cursor spelling)
         (get-type-or-create-variant scope
                                     (. cursor underlying_typedef_type)
                                     :keep-enum True)))

(defn add-struct [^CInterface scope ^(. clang cindex Cursor) cursor]
  (setv struct-name (. cursor type spelling))
  (when (.startswith struct-name "struct ")
    (setv struct-name (cut struct-name (len "struct "))))
  (setv struct (type struct-name (tuple [(. ctypes Structure)]) (dict)))
  (assoc (. scope types) struct-name struct)
  (setv (. struct _fields_) (list (map (fn [c] (tuple [(. c spelling) (get-type-or-create-variant scope (. c type))]))
                                       ;; TODO Handle non fields things
                                       (filter (fn [x] (= (. x kind) (. clang cindex CursorKind FIELD_DECL)))
                                               (.get_children cursor))))))

(defn add-union [^CInterface scope ^(. clang cindex Cursor) cursor]
  (setv union-name (. cursor type spelling))
  (when (.startswith union-name "union ")
    (setv union-name (cut union-name (len "union "))))
  (setv union (type union-name (tuple [(. ctypes Union)]) (dict)))
  (assoc (. scope types) union-name union)
  (setv (. union _fields_) (list (map (fn [c] (tuple [(. c spelling) (get-type-or-create-variant scope (. c type))]))
                                      ;; TODO Handle non fields things
                                      (filter (fn [x] (= (. x kind) (. clang cindex CursorKind FIELD_DECL)))
                                              (.get_children cursor))))))

(defn add-enum [^CInterface scope ^(. clang cindex Cursor) cursor]
  (setv enum-name (. cursor type spelling))
  (when (.startswith enum-name "enum ")
    (setv enum-name (cut enum-name (len "enum "))))
  (assoc (. scope types)
         enum-name
         (.IntEnum enum
                   enum-name
                   (->
                     (map (fn [c] (do
                                    (assert (= (. clang cindex CursorKind ENUM_CONSTANT_DECL)
                                               (. c kind)))
                                    (. c spelling)))
                          (.get_children cursor))
                     list))))

(defn add-var [^CInterface scope ^(. clang cindex Cursor) cursor]
  (setv var-type (get-type-or-create-variant scope (. cursor type)))
  (assoc (. scope symbols) (. cursor spelling) var-type))

(defn add-function [^CInterface scope ^(. clang cindex Cursor) cursor]
  ;; TODO: Handle stdcall
  ;; TODO: Handle "..."
  (setv function (.CFUNCTYPE ctypes
                             (->> (. cursor result_type)
                                  (get-type-or-create-variant scope))
                             (->> cursor
                                  .get_arguments
                                  (map (fn [x] (->> (. x type)
                                                    (get-type-or-create-variant scope))))
                                  unpack-iterable)))
  (assoc (. scope symbols) (. cursor spelling) function))

(defn handle-decleration [^CInterface scope ^(. clang cindex Cursor) cursor]
  ;; Use a macro?
  (cond [(= (. cursor kind) (. clang cindex CursorKind TYPEDEF_DECL)) (add-typedef scope cursor)]
        [(= (. cursor kind) (. clang cindex CursorKind STRUCT_DECL)) (add-struct scope cursor)]
        [(= (. cursor kind) (. clang cindex CursorKind UNION_DECL)) (add-union scope cursor)]
        [(= (. cursor kind) (. clang cindex CursorKind ENUM_DECL)) (add-enum scope cursor)]
        [(= (. cursor kind) (. clang cindex CursorKind VAR_DECL)) (add-var scope cursor)]
        [(= (. cursor kind) (. clang cindex CursorKind FUNCTION_DECL)) (add-function scope cursor)]
        [True (for [c (.get_children cursor)]
                (handle-decleration scope c))]))

(defn parse-header ^CInterface [^(. pathlib Path) header]
  (setv scope (CInterface (defaultdict (fn [] __unknown_type) (dict))
                          (dict))
        index ((. clang cindex Index create))
        tu ((. index parse) header)
        cursor (. tu cursor))
  (handle-decleration scope cursor)
  (assert (->> (in "" (.keys (. scope types)))
               not))
  scope)
