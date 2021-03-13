import ctypes
import c_import

import pytest

@pytest.mark.parametrize('line,name,expected', [
    ('extern char global;', 'global', ctypes.c_char),
    ('extern signed char global;', 'global', ctypes.c_char),

    ('extern unsigned char global;', 'global', ctypes.c_ubyte),

    ('extern short global;', 'global', ctypes.c_short),
    ('extern short int global;', 'global', ctypes.c_short),
    ('extern signed short int global;', 'global', ctypes.c_short),
    ('extern signed short global;', 'global', ctypes.c_short),

    ('extern unsigned short global;', 'global', ctypes.c_ushort),
    ('extern unsigned short int global;', 'global', ctypes.c_ushort),

    ('extern int global;', 'global', ctypes.c_int),
    ('extern signed global;', 'global', ctypes.c_int),
    ('extern signed int global;', 'global', ctypes.c_int),

    ('extern unsigned int global;', 'global', ctypes.c_uint),
    ('extern unsigned global;', 'global', ctypes.c_uint),

    ('extern long global;', 'global', ctypes.c_long),
    ('extern long int global;', 'global', ctypes.c_long),
    ('extern signed long global;', 'global', ctypes.c_long),
    ('extern signed long int global;', 'global', ctypes.c_long),

    ('extern unsigned long global;', 'global', ctypes.c_ulong),
    ('extern unsigned long int global;', 'global', ctypes.c_ulong),

    ('extern long long global;', 'global', ctypes.c_longlong),
    ('extern long long int global;', 'global', ctypes.c_longlong),
    ('extern signed long long global;', 'global', ctypes.c_longlong),
    ('extern signed long long int global;', 'global', ctypes.c_longlong),

    ('extern unsigned long long global;', 'global', ctypes.c_ulonglong),
    ('extern unsigned long long int global;', 'global', ctypes.c_ulonglong),

    ('extern float global;', 'global', ctypes.c_float),

    ('extern double global;', 'global', ctypes.c_double),

    ('extern long double global;', 'global', ctypes.c_longdouble),

    ('extern int* global;', 'global', ctypes.POINTER(ctypes.c_int)),
    ('extern int* const global;', 'global', ctypes.POINTER(ctypes.c_int)),
    ('extern const int* const global;', 'global', ctypes.POINTER(ctypes.c_int)),
    ('extern int const * const global;', 'global', ctypes.POINTER(ctypes.c_int)),
    ('extern int const * global;', 'global', ctypes.POINTER(ctypes.c_int)),

    ('extern void* global;', 'global', ctypes.c_void_p),
    ('extern void* const global;', 'global', ctypes.c_void_p),
    ('extern const void* const global;', 'global', ctypes.c_void_p),
    ('extern void const * const global;', 'global', ctypes.c_void_p),
    ('extern void const * global;', 'global', ctypes.c_void_p),

    ('extern int global[34];', 'global', ctypes.ARRAY(ctypes.c_int, 34)),
    ('extern int global[2][34];', 'global', ctypes.ARRAY(ctypes.ARRAY(ctypes.c_int, 34), 2)),

    ('foo();', 'foo', ctypes.CFUNCTYPE(ctypes.c_int)),
    ('int foo();', 'foo', ctypes.CFUNCTYPE(ctypes.c_int)),
    ('int foo(void);', 'foo', ctypes.CFUNCTYPE(ctypes.c_int)),
    ('void foo(void);', 'foo', ctypes.CFUNCTYPE(None)),
    ('void foo();', 'foo', ctypes.CFUNCTYPE(None)),
    ('void foo(int);', 'foo', ctypes.CFUNCTYPE(None, ctypes.c_int)),
    ('int *foo(int);', 'foo', ctypes.CFUNCTYPE(ctypes.POINTER(ctypes.c_int), ctypes.c_int)),
    ('void foo(int*);', 'foo', ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_int))),
    ('void foo(int, int, int, int);', 'foo', ctypes.CFUNCTYPE(None,
                                                              ctypes.c_int,
                                                              ctypes.c_int,
                                                              ctypes.c_int,
                                                              ctypes.c_int)),
    ('void foo(int, double, float, short);', 'foo', ctypes.CFUNCTYPE(None,
                                                                     ctypes.c_int,
                                                                     ctypes.c_double,
                                                                     ctypes.c_float,
                                                                     ctypes.c_short)),
    ('long foo(int, double, float, short);', 'foo', ctypes.CFUNCTYPE(ctypes.c_long,
                                                                     ctypes.c_int,
                                                                     ctypes.c_double,
                                                                     ctypes.c_float,
                                                                     ctypes.c_short)),
])
def test_symbol(tmpdir, line, name, expected):
    header = tmpdir / 'header.h'
    header.write(line)
    _, symbols = c_import.header_parser.parse_header(header)
    assert symbols[name] == expected
