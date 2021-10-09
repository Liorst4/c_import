import ctypes
import c_import
import typing

import pytest

# TODO: Compiler builtins


def types_are_equivalent(a, b) -> bool:

    if a is None:
        return a == b

    if issubclass(a, ctypes._Pointer):
        while issubclass(a, ctypes._Pointer):
            a = a._type_
            b = b._type_
        return types_are_equivalent(a, b)

    if any((issubclass(o, ctypes._CFuncPtr) for o in (a, b))):
        if not types_are_equivalent(a._restype_, b._restype_):
            return False
        if len(a._argtypes_) != len(b._argtypes_):
            return False
        for (a_arg, b_arg) in zip(a._argtypes_, b._argtypes_):
            if not types_are_equivalent(a_arg, b_arg):
                return False
        return True


    if issubclass(a, (ctypes.Structure, ctypes.Union)):

        if a.__bases__ != b.__bases__:
            return False

        if a.__name__ != b.__name__:
            return False

        if not hasattr(a, "_fields_") and not hasattr(b, "_fields_"):
            return True

        if len(a._fields_) != len(b._fields_):
            return False

        if any((hasattr(o, "_pack_") for o in (a, b))):
            if a._pack_ != b._pack_:
                return False

        for (f_a, f_b) in zip(a._fields_, b._fields_):

            if len(f_a) != len(f_b):
                return False

            f_a_name = f_a[0]
            f_a_type = f_a[1]

            f_b_name = f_b[0]
            f_b_type = f_b[1]

            if len(f_a) == 3:
                if f_a[2] != f_b[2]:
                    return False

            if f_a_name != f_b_name or \
               not types_are_equivalent(f_a_type, f_b_type):
                return False
        return True

    return a == b


# Example classes used in parametrize
opaque_types_types = {
    'thing': type('thing', (ctypes.Structure,), {}),
    'thing2': type(
        'thing2',
        (ctypes.Structure,),
        {'_fields_': [
            ('x', ctypes.c_int),
            ('y', ctypes.c_int),
        ]}
    ),
}
opaque_types_types['thing_ptr'] = ctypes.POINTER(
    opaque_types_types['thing']
)
opaque_types_types['thing2_ptr'] = ctypes.POINTER(
    opaque_types_types['thing2']
)
pointer_typedefs_types = {
    'int_ptr': ctypes.POINTER(ctypes.c_int),
    'float_ptr': ctypes.POINTER(ctypes.c_float),
    'void_ptr': ctypes.c_void_p,
    's': type('s', (ctypes.Structure,), {}),
    'u': type('u', (ctypes.Union,), {}),
    'e': ctypes.c_int,
    'e_ptr': ctypes.POINTER(ctypes.c_int)
}
pointer_typedefs_types['s_ptr'] = ctypes.POINTER(
    pointer_typedefs_types['s']
)
pointer_typedefs_types['u_ptr'] = ctypes.POINTER(
    pointer_typedefs_types['u']
)
structs_and_symbols_types = {
    's': type('s', (ctypes.Structure,), {
        '_fields_': [
            ('a', ctypes.c_float),
            ('b', ctypes.c_double),
        ],
    }),
    'opaque_thing': type('opaque_thing', (ctypes.Structure,), {}),
}
structs_and_symbols_s_ptr = ctypes.POINTER(
    structs_and_symbols_types['s']
)
structs_and_symbols_opaque_thing_ptr = ctypes.POINTER(
    structs_and_symbols_types['opaque_thing'],
)
structs_and_symbols_symbols = {
    'global1': structs_and_symbols_types['s'],
    'global2': structs_and_symbols_s_ptr,
    'global3': structs_and_symbols_opaque_thing_ptr,
    'foo1': ctypes.CFUNCTYPE(None, structs_and_symbols_types['s']),
    'foo2': ctypes.CFUNCTYPE(structs_and_symbols_types['s']),
    'foo3': ctypes.CFUNCTYPE(
        structs_and_symbols_types['s'],
        structs_and_symbols_types['s']
    ),
    'foo4': ctypes.CFUNCTYPE(
        None,
        structs_and_symbols_s_ptr,
    ),
    'foo5': ctypes.CFUNCTYPE(structs_and_symbols_s_ptr),
    'foo6': ctypes.CFUNCTYPE(
        structs_and_symbols_s_ptr,
        structs_and_symbols_s_ptr,
    ),
    'foo7': ctypes.CFUNCTYPE(
        None,
        structs_and_symbols_opaque_thing_ptr
    ),
    'foo8': ctypes.CFUNCTYPE(
        structs_and_symbols_opaque_thing_ptr
    ),
    'foo9': ctypes.CFUNCTYPE(
        structs_and_symbols_opaque_thing_ptr,
        structs_and_symbols_opaque_thing_ptr
    ),
}
unions_and_symbols_types = {
    'u': type('u', (ctypes.Union,), {
        '_fields_': [
            ('a', ctypes.c_float),
            ('b', ctypes.c_double),
        ],
    }),
}
unions_and_symbols_u_ptr = ctypes.POINTER(
    unions_and_symbols_types['u']
)
unions_and_symbols_symbols = {
    'global1': unions_and_symbols_types['u'],
    'global2': unions_and_symbols_u_ptr,

    'foo1': ctypes.CFUNCTYPE(None, unions_and_symbols_types['u']),
    'foo2': ctypes.CFUNCTYPE(unions_and_symbols_types['u']),
    'foo3': ctypes.CFUNCTYPE(
        unions_and_symbols_types['u'],
        unions_and_symbols_types['u']
    ),

    'foo4': ctypes.CFUNCTYPE(None, unions_and_symbols_u_ptr),
    'foo5': ctypes.CFUNCTYPE(unions_and_symbols_u_ptr),
    'foo6': ctypes.CFUNCTYPE(
        unions_and_symbols_u_ptr,
        unions_and_symbols_u_ptr,
    ),
}
enums_and_symbols_types = {
    'e': ctypes.c_int,
}
enums_and_symbols_symbols = {
    'global1': ctypes.c_int,
    'global2': ctypes.POINTER(ctypes.c_int),

    'foo1': ctypes.CFUNCTYPE(None, ctypes.c_int),
    'foo2': ctypes.CFUNCTYPE(ctypes.c_int),
    'foo3': ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_int,
    ),

    'foo4': ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_int)),
    'foo5': ctypes.CFUNCTYPE(ctypes.POINTER(ctypes.c_int)),
    'foo6': ctypes.CFUNCTYPE(
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_int),
    ),
}
opaque_unions_types = {
    'u': type('u', (ctypes.Union,), {}),
    'u2': type('u2', (ctypes.Union,), {
        '_fields_': [
            ('a', ctypes.c_float),
            ('b', ctypes.c_double),
        ]
    })
}
opaque_unions_types['u2_ptr'] = ctypes.POINTER(opaque_unions_types['u2'])

test_header_cases = (
    (
        # empty header
        (
            '',
            {},
            {},
            {},
        ),

        # basic type symbols
        (
'''
    char global1;
    signed char global2;

    unsigned char global3;

    short global4;
    short int global5;
    signed short int global6;
    signed short global7;

    unsigned short global8;
    unsigned short int global9;

    int global10;
    signed global11;
    signed int global12;

    unsigned int global13;
    unsigned global14;

    long global15;
    long int global16;
    signed long global17;
    signed long int global18;

    unsigned long global19;
    unsigned long int global20;

    long long global21;
    long long int global22;
    signed long long global23;
    signed long long int global24;

    unsigned long long global25;
    unsigned long long int global26;

    float global27;

    double global28;

    long double global29;

    int* global30;
    int* const global31;
    const int* const global32;
    int const * const global33;
    int const * global34;

    void* global35;
    void* const global36;
    const void* const global37;
    void const * const global38;
    void const * global39;

    int global40[34];
    int global41[2][34];

    char* global42;

    volatile double global43;
    double volatile global44;

    double *restrict global45;

    double global46, global47, *global48, global49;

    foo1();
    int foo2();
    int foo3(void);

    void foo4(void);
    void foo5();

    void foo6(int);

    int *foo7(int);

    void foo8(int*);

    void foo9(int, int, int, int);

    void foo10(int, double, float, short);

    long foo11(int, double, float, short);

    int (*foo12) (long);

    char* foo13(void);

    const char* foo14(void);
    char const* foo15(void);

    void foo16(double arg[]);
''',
            {
            },
            {
                'global1': ctypes.c_char,
                'global2': ctypes.c_char,

                'global3': ctypes.c_ubyte,

                'global4': ctypes.c_short,
                'global5': ctypes.c_short,
                'global6': ctypes.c_short,
                'global7': ctypes.c_short,

                'global8': ctypes.c_ushort,
                'global9': ctypes.c_ushort,

                'global10': ctypes.c_int,
                'global11': ctypes.c_int,
                'global12': ctypes.c_int,

                'global13': ctypes.c_uint,
                'global14': ctypes.c_uint,

                'global15': ctypes.c_long,
                'global16': ctypes.c_long,
                'global17': ctypes.c_long,
                'global18': ctypes.c_long,

                'global19': ctypes.c_ulong,
                'global20': ctypes.c_ulong,

                'global21': ctypes.c_longlong,
                'global22': ctypes.c_longlong,
                'global23': ctypes.c_longlong,
                'global24': ctypes.c_longlong,

                'global25': ctypes.c_ulonglong,
                'global26': ctypes.c_ulonglong,

                'global27': ctypes.c_float,

                'global28': ctypes.c_double,

                'global29': ctypes.c_longdouble,

                'global30': ctypes.POINTER(ctypes.c_int),
                'global31': ctypes.POINTER(ctypes.c_int),
                'global32': ctypes.POINTER(ctypes.c_int),
                'global33': ctypes.POINTER(ctypes.c_int),
                'global34': ctypes.POINTER(ctypes.c_int),

                'global35': ctypes.c_void_p,
                'global36': ctypes.c_void_p,
                'global37': ctypes.c_void_p,
                'global38': ctypes.c_void_p,
                'global39': ctypes.c_void_p,

                'global40': ctypes.ARRAY(ctypes.c_int, 34),
                'global41': ctypes.ARRAY(ctypes.ARRAY(ctypes.c_int, 34), 2),

                'global42': ctypes.POINTER(ctypes.c_char),

                'global43': ctypes.c_double,
                'global44': ctypes.c_double,

                'global45': ctypes.POINTER(ctypes.c_double),

                'global46': ctypes.c_double,
                'global47': ctypes.c_double,
                'global48': ctypes.POINTER(ctypes.c_double),
                'global49': ctypes.c_double,

                'foo1': ctypes.CFUNCTYPE(ctypes.c_int),
                'foo2': ctypes.CFUNCTYPE(ctypes.c_int),
                'foo3': ctypes.CFUNCTYPE(ctypes.c_int),

                'foo4': ctypes.CFUNCTYPE(None),
                'foo5': ctypes.CFUNCTYPE(None),

                'foo6': ctypes.CFUNCTYPE(None, ctypes.c_int),
                'foo7': ctypes.CFUNCTYPE(ctypes.POINTER(ctypes.c_int), ctypes.c_int),
                'foo8':ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_int)),
                'foo9':ctypes.CFUNCTYPE(None,
                                        ctypes.c_int,
                                        ctypes.c_int,
                                        ctypes.c_int,
                                        ctypes.c_int),
                'foo10': ctypes.CFUNCTYPE(None,
                                          ctypes.c_int,
                                          ctypes.c_double,
                                          ctypes.c_float,
                                          ctypes.c_short),
                'foo11': ctypes.CFUNCTYPE(ctypes.c_long,
                                          ctypes.c_int,
                                          ctypes.c_double,
                                          ctypes.c_float,
                                          ctypes.c_short),
                'foo12': ctypes.POINTER(ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_long)),
                'foo13': ctypes.CFUNCTYPE(ctypes.POINTER(ctypes.c_char)),
                'foo14': ctypes.CFUNCTYPE(ctypes.POINTER(ctypes.c_char)),
                'foo15': ctypes.CFUNCTYPE(ctypes.POINTER(ctypes.c_char)),
                'foo16': ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_double)),
            },
            {},
        ),

        # basic typedef
        (
'''
typedef int thing;
thing my_thing;
''',
            {
                'thing': ctypes.c_int,
            },
            {
                'my_thing': ctypes.c_int,
            },
            {},
        ),

        # empty struct
        (
            "struct thing {};",
            {
                'thing': type(
                    "thing",
                    (ctypes.Structure,),
                    {}
                ),
            },
            {},
            {},
        ),

        # struct with one field
        (
'''
struct thing {
    int x;
};
''',
            {
                'thing': type(
                    "thing",
                    (ctypes.Structure,),
                    {
                        '_fields_': [("x", ctypes.c_int)],
                    },
                ),
            },
            {},
            {},
        ),


        # empty union
        (
            "union x {};",
            {
                'x': type('x', (ctypes.Union,), {})
            },
            {},
            {},
        ),

        # basic union
        (
'''
union x {
    int y;
    char z;
};
''',
            {
                'x': type(
                    'x',
                    (ctypes.Union,),
                    {
                        '_fields_': [
                            ('y', ctypes.c_int),
                            ('z', ctypes.c_char),
                        ],
                    }
                ),
            },
            {},
            {},
        ),

        # Void typedef
        (
'''
typedef void my_type;
typedef my_type *my_type_pointer;
''',
            {
                'my_type': None,
                'my_type_pointer': ctypes.c_void_p,
            },
            {},
            {},
        ),

        # basic enum
        (
'''
enum thing {
   A,
   B,
   C,
};
''',
            {
                'thing': ctypes.c_int,
            },
            {},
            {
                'A': 0,
                'B': 1,
                'C': 2,
            },
        ),

        # Functions with enums
        (
'''
enum thing {
   A,
   B,
   C,
};

typedef enum {
    H,
    I,
    J
} other_thing;

enum thing func1(void);
void func2(enum thing argument);
other_thing func3(void);
void func4(other_thing x);
''',
            {
                'thing': ctypes.c_int,
                'other_thing': ctypes.c_int,
            },
            {
                'func1': ctypes.CFUNCTYPE(ctypes.c_int),
                'func2': ctypes.CFUNCTYPE(None, ctypes.c_int),
                'func3': ctypes.CFUNCTYPE(ctypes.c_int),
                'func4': ctypes.CFUNCTYPE(None, ctypes.c_int),
            },
            {
                'A': 0,
                'B': 1,
                'C': 2,
                'H': 0,
                'I': 1,
                'J': 2,
            },
        ),

        # Typedef for anon stuff
        (
'''
typedef struct {
    int x;
    double y;
} my_struct_t;

typedef union {
    int x;
    double y;
} my_union_u;

typedef enum {
    X,
    Y
} my_enum_e;
''',
            {
                'my_struct_t': type(
                    'my_struct_t',
                    (ctypes.Structure,),
                    {
                        '_fields_': [
                            ('x', ctypes.c_int),
                            ('y', ctypes.c_double)
                        ],
                    },
                ),
                'my_union_u': type(
                    'my_union_u',
                    (ctypes.Union,),
                    {
                        '_fields_': [
                            ('x', ctypes.c_int),
                            ('y', ctypes.c_double)
                        ],
                    },
                ),
                'my_enum_e': ctypes.c_int,
            },
            {},
            {
                'X': 0,
                'Y': 1,
            },
        ),

        # pointer typedefs
        (
'''
typedef int* int_ptr;
typedef float* float_ptr;
typedef void* void_ptr;

struct s {};
typedef struct s* s_ptr;

union u {};
typedef union u* u_ptr;

enum e {};
typedef enum e* e_ptr;
''',
            pointer_typedefs_types.copy(),
            {},
            {},
        ),

        # opaque type
        (
'''
struct thing;
typedef struct thing* thing_ptr;

struct thing2;
typedef struct thing2* thing2_ptr;
struct thing2 {
    int x;
    int y;
};
''',
            opaque_types_types.copy(),
            {},
            {},
        ),

        # typedef of function pointer
        (
'''
typedef float (*callback_t)(int, float, void*);
''',
            {
                'callback_t': ctypes.POINTER(ctypes.CFUNCTYPE(
                    ctypes.c_float,
                    ctypes.c_int,
                    ctypes.c_float,
                    ctypes.c_void_p
                )),
            },
            {},
            {},
        ),

        # struct with bitfields
        (
'''
struct s {
    int a : 16;
    int b : 1;
    short c : 5;
};
''',
            {
                's': type('s', (ctypes.Structure,), {
                    '_fields_': [
                        ('a', ctypes.c_int, 16),
                        ('b', ctypes.c_int, 1),
                        ('c', ctypes.c_short, 5),
                    ],
                })
            },
            {},
            {},
        ),

        # packed structs
        (
'''
struct s {
    int a;
    short b;
    char c;
    long long d;
} __attribute__((packed));
''',
            {
                's': type('s', (ctypes.Structure,), {
                    '_pack_': 1,
                    '_fields_': [
                        ('a', ctypes.c_int),
                        ('b', ctypes.c_short),
                        ('c', ctypes.c_char),
                        ('d', ctypes.c_longlong),
                    ],
                }),
            },
            {},
            {},
        ),

        # Structs and symbols
        (
'''
struct s {
    float a;
    double b;
};

struct opaque_thing;

struct s global1;
struct s *global2;
struct opaque_thing *global3;

void foo1(struct s x);
struct s foo2(void);
struct s foo3(struct s x);

void foo4(struct s* x);
struct s* foo5(void);
struct s* foo6(struct s* x);

void foo7(struct opaque_thing* x);
struct opaque_thing* foo8(void);
struct opaque_thing* foo9(struct opaque_thing* x);
''',
            structs_and_symbols_types,
            structs_and_symbols_symbols,
            {},
        ),

        # Union and symbols
        (
'''
union u {
    float a;
    double b;
};

union u global1;
union u* global2;

void foo1(union u x);
union u foo2(void);
union u foo3(union u x);

void foo4(union u* x);
union u* foo5(void);
union u* foo6(union u* x);
''',
            unions_and_symbols_types,
            unions_and_symbols_symbols,
            {},
        ),

        # Enums and symbols
        (
'''
enum e {
    A,
    B,
    C,
};

enum e global1;
enum e* global2;

void foo1(enum e x);
enum e foo2(void);
enum e foo3(enum e x);

void foo4(enum e* x);
enum e* foo5(void);
enum e* foo6(enum e* x);
''',
            enums_and_symbols_types,
            enums_and_symbols_symbols,
            {
                'A': 0,
                'B': 1,
                'C': 2,
            },
        ),

        # Opaque enum
        (
'''
enum e;
enum e2;
enum e2 {
    A,
    B,
    C,
};
''',
            {
                'e': ctypes.c_int,
                'e2': ctypes.c_int,
            },
            {},
            {
                'A': 0,
                'B': 1,
                'C': 2,
            },
        ),

        # Opaque union
        (
'''
union u;
union u2;
typedef union u2* u2_ptr;
union u2 {
    float a;
    double b;
};
''',
            opaque_unions_types,
            {},
            {},
        ),

        # sizeof usage
        (
'''
double a;
char b[sizeof(a)];
''',
            {},
            {
                'a': ctypes.c_double,
                'b': ctypes.ARRAY(ctypes.c_char, ctypes.sizeof(ctypes.c_double)),
            },
            {},
        ),
    ),
    (
        'empty header',
        'basic type symbols',
        'basic typedef',
        'empty struct',
        'struct with one field',
        'empty union',
        'basic union',
        'void typedef',
        'basic enum',
        'functions with enums',
        'typedef of anonymous stuff',
        'pointer typedefs',
        'opaque types',
        'typedef of function pointer',
        'struct with bitfields',
        'packed structs',
        'structs and symbols',
        'unions and symbols',
        'enums and symbols',
        'opaque enum',
        'opaque unions',
        'sizeof usage'
    )
)
@pytest.mark.parametrize(
    'header_content,expected_types,expected_symbols,expected_enum_consts',
    test_header_cases[0],
    ids=test_header_cases[1])
def test_header(tmpdir,
                header_content: str,
                expected_types,
                expected_symbols,
                expected_enum_consts,
):

    header = tmpdir / 'header.h'
    header.write(header_content)
    types, symbols, enum_consts = c_import.header_parser.parse_header(header)

    # Test types
    assert set(types.keys()) == set(expected_types.keys())
    for (key, value) in types.items():
        assert types_are_equivalent(value, expected_types[key])

    # Test symbols
    assert set(symbols.keys()) == set(expected_symbols.keys())
    for (key, value) in symbols.items():
        assert types_are_equivalent(value, expected_symbols[key])

    assert enum_consts == expected_enum_consts

def test_struct_with_self_reference(tmpdir):
    header_content = '''
struct node;
struct node {
    struct node* next;
};
'''
    header = tmpdir / 'header.h'
    header.write(header_content)
    types, _, _ = c_import.header_parser.parse_header(header)
    assert 'node' in types
    assert issubclass(types['node'], ctypes.Structure)
    assert types['node']._fields_[0][0] == 'next'
    assert issubclass(types['node']._fields_[0][1], ctypes._Pointer)
    assert types['node']._fields_[0][1]._type_ == types['node']
    assert types['node']._fields_[0][1]._type_._fields_[0][0] == 'next'

def test_builtin_record(tmpdir):
    header_content = 'typedef __builtin_va_list thingy;'
    header = tmpdir / 'header.h'
    header.write(header_content)
    types, _, _ = c_import.header_parser.parse_header(header)
    assert 'thingy' in types
    assert types['thingy'] is not None
    assert any(issubclass(types['thingy'], x) for x in (
        ctypes.Structure,
        ctypes.Union,
        ctypes._Pointer,
        ctypes.Array
    ))


def test_types_with_unbounded_nested_anonymous_types(tmpdir):
    header_content = '''
struct s {
    union {
        int x;
        long long int y;
    };
    double z;
    struct {
        int a;
        int b;
    };
};

union u {
    union {
        int x;
        long long int y;
    };
    double z;
    struct {
        int a;
        int b;
    };
};
'''
    header = tmpdir / 'header.h'
    header.write(header_content)
    types, _, _ = c_import.header_parser.parse_header(header)

    assert 's' in types
    assert issubclass(types['s'], ctypes.Structure)
    assert types['s']._anonymous_
    instance = types['s'](x=5, z=3.5, a=4, b=8)
    for i in ('x', 'y', 'z', 'a', 'b'):
        assert hasattr(instance, i)
    assert instance.x == instance.y

    assert 'u' in types
    assert issubclass(types['u'], ctypes.Union)
    assert types['u']._anonymous_
    instance2 = types['u']()
    for i in ('x', 'y', 'z', 'a', 'b'):
        assert hasattr(instance2, i)


def test_types_with_bounded_nested_anonymous_types(tmpdir):
    header_content = '''
struct other_type {
    char cc;
    char yy;
};

struct s {
    struct {
        int x;
        long long int y;
        struct other_type t;
    } a;
    double b;
    struct {
        float f;
        double d;
    } *d, e[10], c;
};

union u {
    struct {
        int x;
        long long int y;
        struct other_type t;
    } a;
    double b;
    struct {
        float f;
        double d;
    } *d, e[10], c;
};
'''
    header = tmpdir / 'header.h'
    header.write(header_content)
    types, _, _ = c_import.header_parser.parse_header(header)

    assert 'other_type' in types
    class other_type(ctypes.Structure):
        _fields_ = [('cc', ctypes.c_char),
                    ('yy', ctypes.c_char)]
    assert types_are_equivalent(types['other_type'], other_type)

    assert 's' in types
    assert issubclass(types['s'], ctypes.Structure)
    instance = types['s']()
    instance.d = ctypes.pointer(instance.c)
    assert isinstance(instance.a, ctypes.Structure)
    assert isinstance(instance.b, (ctypes.c_double, float))
    assert isinstance(instance.c, ctypes.Structure)
    assert issubclass(instance.d._type_, ctypes.Structure)
    assert isinstance(instance.e, ctypes.Array)
    assert len(instance.e) == 10
    for i in ('x','y', 't'):
        assert hasattr(instance.a, i)
    assert instance.a.t.__class__.__name__ == "other_type"
    for i in ('f','d'):
        assert hasattr(instance.c, i)
    for i in ('f','d'):
        assert hasattr(instance.d.contents, i)
    for i in ('f','d'):
        assert hasattr(instance.e[0], i)

    assert 'u' in types
    assert issubclass(types['u'], ctypes.Union)
    instance2 = types['u']()
    assert isinstance(instance2.a, ctypes.Structure)
    assert isinstance(instance2.b, (ctypes.c_double, float))
    assert isinstance(instance2.c, ctypes.Structure)
    assert issubclass(instance2.d._type_, ctypes.Structure)
    assert isinstance(instance2.e, ctypes.Array)
    assert len(instance2.e) == 10
    for i in ('x','y', 't'):
        assert hasattr(instance2.a, i)
    assert instance2.a.t.__class__.__name__ == "other_type"
    for i in ('f','d'):
        assert hasattr(instance2.c, i)
    for i in ('f','d'):
        assert hasattr(instance2.e[0], i)
    instance3 = types['u']()
    instance3.c.f = 1
    instance3.c.d = 2
    instance2.d = ctypes.pointer(instance3.c)
    for i in ('f','d'):
        assert hasattr(instance2.d.contents, i)
    assert instance2.d.contents.f == 1
    assert instance2.d.contents.d == 2


def test_symbols_with_anonymous_types(tmpdir):
    header_content = '''
struct {
    int x;
    float y;
} g1;

struct {
    int x;
    float y;
} g2, *g3;

union {
    int x;
    float y;
} g4;

union {
    int x;
    float y;
} g5, *g6;

enum {
    A,
    B,
    C,
} g7;

enum {
    E,
    F,
    G,
} g8, *g9;
'''
    header = tmpdir / 'header.h'
    header.write(header_content)
    _, symbols, _ = c_import.header_parser.parse_header(header)
    for i in range(1,10):
        assert f'g{i}' in symbols

    assert issubclass(symbols['g1'], ctypes.Structure)
    assert symbols['g1']._fields_ == [
        ('x', ctypes.c_int),
        ('y', ctypes.c_float)
    ]

    assert issubclass(symbols['g2'], ctypes.Structure)
    assert symbols['g2']._fields_ == [
        ('x', ctypes.c_int),
        ('y', ctypes.c_float)
    ]

    assert issubclass(symbols['g3'], ctypes._Pointer)
    assert issubclass(symbols['g3']._type_, ctypes.Structure)
    assert symbols['g3']._type_._fields_ == [
        ('x', ctypes.c_int),
        ('y', ctypes.c_float)
    ]

    assert issubclass(symbols['g4'], ctypes.Union)
    assert symbols['g4']._fields_ == [
        ('x', ctypes.c_int),
        ('y', ctypes.c_float)
    ]

    assert issubclass(symbols['g5'], ctypes.Union)
    assert symbols['g5']._fields_ == [
        ('x', ctypes.c_int),
        ('y', ctypes.c_float)
    ]

    assert issubclass(symbols['g6'], ctypes._Pointer)
    assert issubclass(symbols['g6']._type_, ctypes.Union)
    assert symbols['g6']._type_._fields_ == [
        ('x', ctypes.c_int),
        ('y', ctypes.c_float)
    ]

    assert symbols['g7'] == ctypes.c_int
    assert symbols['g8'] == ctypes.c_int
    assert symbols['g9'] == ctypes.POINTER(ctypes.c_int)
