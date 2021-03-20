(import ctypes
        pathlib
        [collections [defaultdict]]
        [typing [Dict Callable Tuple NamedTuple]])

(import clang.cindex)

(setv PointerWrapper (of Callable [int] object)
      TypeTable (of Dict str PointerWrapper)
      SymbolTable (of Dict str PointerWrapper)
      ^TypeTable INITIAL_TYPES (dict))

(assoc INITIAL_TYPES
       "char" (. ctypes c_char)
       "signed char" (. ctypes c_char)
       "unsigned char" (. ctypes c_ubyte)
       "short" (. ctypes c_short)
       "short int" (. ctypes c_short)
       "signed short" (. ctypes c_short)
       "signed short int" (. ctypes c_short)
       "unsigned short" (. ctypes c_ushort)
       "unsigned short int" (. ctypes c_ushort)
       "int" (. ctypes c_int)
       "signed" (. ctypes c_int)
       "signed int" (. ctypes c_int)
       "unsigned" (. ctypes c_uint)
       "unsigned int" (. ctypes c_uint)
       "long" (. ctypes c_long)
       "long int" (. ctypes c_long)
       "signed long" (. ctypes c_long)
       "signed long int" (. ctypes c_long)
       "unsigned long" (. ctypes c_ulong)
       "unsigned long int" (. ctypes c_ulong)
       "long long" (. ctypes c_longlong)
       "long long int" (. ctypes c_longlong)
       "signed long long" (. ctypes c_longlong)
       "signed long long int" (. ctypes c_longlong)
       "unsigned long long" (. ctypes c_ulonglong)
       "unsigned long long int" (. ctypes c_ulonglong)
       "float" (. ctypes c_float)
       "double" (. ctypes c_double)
       "long double" (. ctypes c_longdouble))

(defclass CInterface [NamedTuple]
  (setv ^TypeTable types (dict)
        ^SymbolTable symbols (dict)))

(defn get-type-or-create-variant ^PointerWrapper [^CInterface scope ^(. clang cindex Type) clang-type]
  ;; TODO: Handle anonymous and opaque types
  ;; TODO: Handle consts
  (assert (. clang-type spelling))
  (assert (!= "void" (. clang-type spelling)))
  ;; TODO: Use macro for kind switch?
  (cond [(= (. clang-type kind) (. clang cindex TypeKind POINTER))
         (do (setv pointee (.get_pointee clang-type))
             ;; TODO: Bug?
             (if (in (. pointee spelling) ["void" "const void" "void const"])
                 (. ctypes c_void_p)
                 ((. ctypes POINTER) (get-type-or-create-variant scope pointee))))]

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

        [True (get (. scope types) (. clang-type spelling))]))

(defn add-typedef [^CInterface scope ^(. clang cindex Cursor) cursor]
  (assoc (. scope types)
         (. cursor spelling)
         (get-type-or-create-variant scope (. cursor underlying_typedef_type))))

(defn add-struct [^CInterface scope ^(. clang cindex Cursor) cursor]
  (setv struct (type (. cursor spelling) (tuple [(. ctypes Structure)]) (dict)))
  (assoc (. scope types) (. cursor spelling) struct)
  (setv (. struct _fields_) (list (map (fn [c] (tuple [(. c spelling) (get-type-or-create-variant scope (. c type))]))
                                       ;; TODO Handle non fields things
                                       (filter (fn [x] (= (. x kind) (. clang cindex CursorKind FIELD_DECL)))
                                               (.get_children cursor))))))

(defn add-union [^CInterface scope ^(. clang cindex Cursor) cursor]
  (setv union (type (. cursor spelling) (tuple [(. ctypes Union)]) (dict)))
  (assoc (. scope types) (. cursor spelling) union)
  (setv (. union _fields_) (list (map (fn [c] (tuple [(. c spelling) (get-type-or-create-variant scope (. c type))]))
                                      ;; TODO Handle non fields things
                                      (filter (fn [x] (= (. x kind) (. clang cindex CursorKind FIELD_DECL)))
                                              (.get_children cursor))))))

(defn add-enum [^CInterface scope ^(. clang cindex Cursor) cursor]
  ;; TODO use enum library
  (assoc (. scope types) (. cursor spelling) (. ctypes c_int)))

(defn add-var [^CInterface scope ^(. clang cindex Cursor) cursor]
  (setv var-type (get-type-or-create-variant scope (. cursor type)))
  (assoc (. scope symbols) (. cursor spelling) var-type))

(defn add-function [^CInterface scope ^(. clang cindex Cursor) cursor]
  ;; TODO: Handle stdcall
  ;; TODO: Handle "..."
  (setv function ((. ctypes CFUNCTYPE) (if (= "void" (. cursor result_type spelling))
                                           None
                                           (get-type-or-create-variant scope (. cursor result_type)))
                  (unpack-iterable (map (fn [x] (get-type-or-create-variant scope (. x type))) (.get_arguments cursor)))))
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
  (setv scope (CInterface (defaultdict (fn [] (. ctypes c_int)) (dict)) (dict))
        index ((. clang cindex Index create))
        tu ((. index parse) header)
        cursor (. tu cursor))
  (.update (. scope types) (.copy INITIAL_TYPES))
  (handle-decleration scope cursor)
  scope)
