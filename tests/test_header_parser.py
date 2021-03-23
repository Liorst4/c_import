import ctypes
import c_import
import enum

import pytest

# TODO: Test function pointer typedef
# TODO: Test multiple structs

def struct_are_equivalent(a: type, b: type) -> bool:
    if issubclass(a, (ctypes.Structure, ctypes.Union)):
        for (f_a, f_b) in zip(a._fields_, b._fields_):
            f_a_name, f_a_type = f_a
            f_b_name, f_b_type = f_b
            if f_a_name != f_b_name or \
               not struct_are_equivalent(f_a_type, f_b_type):
                return False
        return True
    else:
        return a == b

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
''',
            {
                'const int': ctypes.c_int,
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
                    {
                        '_fields_': [],
                    }
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
                'x': type('x', (ctypes.Union,), {'_fields_': []})
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
''',
            {
                'my_type': None,
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

    # Test symbols
    expected_types.update(c_import.header_parser.INITIAL_TYPES.copy())
    assert set(types.keys()) == set(expected_types.keys())
    for (key, value) in types.items():
        if value and issubclass(value, (ctypes.Structure, ctypes.Union)):
            assert struct_are_equivalent(value, expected_types[key])
        elif value and issubclass(value, enum.Enum):
            assert value.__members__ == expected_types[key].__members__
        else:
            assert value == expected_types[key]

    # Test types
    assert symbols == expected_symbols

