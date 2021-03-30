import ctypes
import c_import
import enum
import typing

import pytest

# TODO: restrict qualifier
# TODO: Compiler builtins


def types_are_equivalent(a, b) -> bool:

    if a is None:
        return a == b

    if issubclass(a, enum.Enum):
        return a.__members__ == b.__members__

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
class struct_with_anon_union(ctypes.Structure):
    class _anon1(ctypes.Union):
        _fields_ = [('x', ctypes.c_int), ('y', ctypes.c_longlong)]
    _anonymous_ = ('_anon1',)
    _fields_=[('_anon1', _anon1), ('z', ctypes.c_double)]
class struct_with_anon_struct_member(ctypes.Structure):
    class _anon1(ctypes.Union):
        _fields_ = [('x', ctypes.c_int), ('y', ctypes.c_longlong)]
    _fields_=[('a', _anon1), ('b', ctypes.c_double)]
symbols_with_anonymous_types_types = {
    '_anon1': type('_anon1', (ctypes.Structure,), {
        '_fields_': [
            ('x', ctypes.c_int),
            ('y', ctypes.c_float),
        ]
    }),
    '_anon2': type('_anon2', (ctypes.Union,), {
        '_fields_': [
            ('x', ctypes.c_int),
            ('y', ctypes.c_float),
        ]
    }),
}
symbols_with_anonymous_types_symbols = {
    'my_global1': symbols_with_anonymous_types_types['_anon1'],
    'my_global2': symbols_with_anonymous_types_types['_anon2'],
}
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
    'e': enum.IntEnum('e', []),
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
    'e': enum.IntEnum('e', ['A', 'B', 'C']),
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

@pytest.mark.parametrize('header_content,expected_types,expected_symbols',
    (
        # empty header
        (
            '',
            {},
            {}
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
            }
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
        ),


        # empty union
        (
            "union x {};",
            {
                'x': type('x', (ctypes.Union,), {})
            },
            {}
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
            {}
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
            {}
        ),

        # enum
        (
'''
enum thing {
   A,
   B,
   C,
};
''',
            {
                'thing': enum.IntEnum('thing', ('A', 'B', 'C')),
            },
            {}
        ),

        # Functions with enums
        (
'''
enum thing {
   A,
   B,
   C,
};

enum thing func1(void);
void func2(enum thing argument);
''',
            {
                'thing': enum.IntEnum('thing', ('A', 'B', 'C')),
            },
            {
                'func1': ctypes.CFUNCTYPE(ctypes.c_int),
                'func2': ctypes.CFUNCTYPE(None, ctypes.c_int),
            }
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
                'my_enum_e': enum.IntEnum('my_enum_e', ['X', 'Y']),
            },
            {}
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
        ),

        # struct with anonymous union members
        (
'''
struct struct_with_anon_union {
    union {
        int x;
        long long int y;
    };
    double z;
};
''',
            {
                'struct_with_anon_union': struct_with_anon_union,
            },
            {}
        ),

        # struct with anonymous struct member
        (
'''
struct struct_with_anon_struct_member {
    struct {
        int x;
        long long int y;
    } a;
    double b;
};
''',
            {
                'struct_with_anon_struct_member': struct_with_anon_struct_member
            },
            {}
        ),

        # symbols with anonymous types
        (
'''
struct {
    int x;
    float y;
} my_global1;

union {
    int x;
    float y;
} my_global2;
''',
            symbols_with_anonymous_types_types.copy(),
            symbols_with_anonymous_types_symbols.copy()
        ),

        # anonymous enum
        (
'''
enum {
    A,
    B,
    C
};
''',
            {
                '_anon1': enum.IntEnum('_anon1', ['A', 'B', 'C']),
            },
            {}
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
            {}
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
            {}
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
            {}
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
            structs_and_symbols_symbols
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
        ),
    ),
    ids=(
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
        'struct with anonymous union members',
        'struct with anonymous struct member',
        'symbols with anonymous types',
        'anonymous enum',
        'typedef of function pointer',
        'struct with bitfields',
        'packed structs',
        'structs and symbols',
        'unions and symbols',
        'enums and symbols',
    )
)
def test_header(tmpdir,
                header_content: str,
                expected_types,
                expected_symbols
):

    header = tmpdir / 'header.h'
    header.write(header_content)
    types, symbols = c_import.header_parser.parse_header(header)

    # Test types
    assert set(types.keys()) == set(expected_types.keys())
    for (key, value) in types.items():
        assert types_are_equivalent(value, expected_types[key])

    # Test symbols
    assert set(symbols.keys()) == set(expected_symbols.keys())
    for (key, value) in symbols.items():
        assert types_are_equivalent(value, expected_symbols[key])

def test_struct_with_self_reference(tmpdir):
    header_content = '''
struct node;
struct node {
    struct node* next;
};
'''
    header = tmpdir / 'header.h'
    header.write(header_content)
    types, _ = c_import.header_parser.parse_header(header)
    assert 'node' in types
    assert issubclass(types['node'], ctypes.Structure)
    assert types['node']._fields_[0][0] == 'next'
    assert issubclass(types['node']._fields_[0][1], ctypes._Pointer)
    assert types['node']._fields_[0][1]._type_ == types['node']
    assert types['node']._fields_[0][1]._type_._fields_[0][0] == 'next'
