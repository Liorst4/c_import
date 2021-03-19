(import ctypes
        pathlib
        [collections [defaultdict]]
        [typing [Dict Callable Tuple]])

(import clang.cindex)

(setv INITIAL_TYPES (dict))
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


(setv PointerWrapper (of Callable [int] object)
      TypeTable (of Dict str PointerWrapper)
      SymbolTable (of Dict str PointerWrapper))

(defn parse-header ^(of Tuple TypeTable SymbolTable) [^(. pathlib Path) header]
  (setv ^SymbolTable symbols (dict)
        ^TypeTable types (defaultdict (fn [] (. ctypes c_int)) (dict))
        index ((. clang cindex Index create))
        tu ((. index parse) header)
        cursor (. tu cursor))
  (.update types (.copy INITIAL_TYPES))

  (defn get-type-or-create-variant [^(. clang cindex Type) cursor]
    ;; TODO: Handle anonymous and opaque types
    ;; TODO: Handle consts
    (assert (. cursor spelling))
    (assert (!= "void" (. cursor spelling)))
    (cond [(= (. cursor kind) (. clang cindex TypeKind POINTER))
           (do (setv pointee (.get_pointee cursor))
               ;; TODO: Bug?
               (if (in (. pointee spelling) ["void" "const void" "void const"])
                   (. ctypes c_void_p)
                   ((. ctypes POINTER) (get-type-or-create-variant pointee))))]

          [(= (. cursor kind) (. clang cindex TypeKind CONSTANTARRAY))
           ((. ctypes ARRAY) (get-type-or-create-variant (. cursor element_type)) (. cursor element_count))]

          [True (get types (. cursor spelling))]))

  (defn handle-typedef [^(. clang cindex Cursor) cursor]
    (setv (get types (. cursor spelling)) (get-type-or-create-variant (. cursor underlying_typedef_type))))

  (defn handle-struct [^(. clang cindex Cursor) cursor]
    (setv struct (type (. cursor spelling) (tuple [(. ctypes Structure)]) (dict))
          (get types (. cursor spelling)) struct
          (. struct _fields_) (list (map (fn [c] (tuple [(. c spelling) (get-type-or-create-variant c)]))
                                         ;; TODO Handle non fields things
                                         (filter (fn [x] (= (. x kind) (. clang cindex CursorKind FIELD_DECL)))
                                                 (.get_children cursor))))))

  (defn handle-union [^(. clang cindex Cursor) cursor]
    (setv union (type (. cursor spelling) (tuple [(. ctypes Union)]) (dict))
          (get types (. cursor spelling)) union
          (. union _fields_) (list (map (fn [c] (tuple [(. c spelling) (get-type-or-create-variant c)]))
                                         ;; TODO Handle non fields things
                                         (filter (fn [x] (= (. x kind) (. clang cindex CursorKind FIELD_DECL)))
                                                 (.get_children cursor))))))

  (defn handle-enum [^(. clang cindex Cursor) cursor]
    ;; TODO use enum library
    (assoc types (. cursor spelling) (. ctypes c_int)))

  (defn handle-var [^(. clang cindex Cursor) cursor]
    (setv var-type (get-type-or-create-variant (. cursor type))
          (get symbols (. cursor spelling)) var-type))

  (defn handle-function [^(. clang cindex Cursor) cursor]
    ;; TODO: Handle stdcall
    ;; TODO: Handle "..."
    (setv function ((. ctypes CFUNCTYPE) (if (= "void" (. cursor result_type spelling))
                                             None
                                             (get-type-or-create-variant (. cursor result_type)))
                    (unpack-iterable (map (fn [x] (get-type-or-create-variant (. x type))) (.get_arguments cursor))))
          (get symbols (. cursor spelling)) function))

  (defn handle-cursor [^(. clang cindex Cursor) cursor]
    (cond [(= (. cursor kind) (. clang cindex CursorKind TYPEDEF_DECL)) (handle-typedef cursor)]
          [(= (. cursor kind) (. clang cindex CursorKind STRUCT_DECL)) (handle-struct cursor)]
          [(= (. cursor kind) (. clang cindex CursorKind UNION_DECL)) (handle-union cursor)]
          [(= (. cursor kind) (. clang cindex CursorKind ENUM_DECL)) (handle-enum cursor)]
          [(= (. cursor kind) (. clang cindex CursorKind VAR_DECL)) (handle-var cursor)]
          [(= (. cursor kind) (. clang cindex CursorKind FUNCTION_DECL)) (handle-function cursor)]
          [True (for [c (.get_children cursor)]
                  (handle-cursor c))]))

  (handle-cursor cursor)
  (tuple [(dict types) symbols]))
