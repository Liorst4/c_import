# Copyright (C) 2023  Lior Stern
#
# This file is part of c_import.
#
# c_import is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# c_import is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with c_import.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import c_import
import ctypes
import pytest
import contextlib

@pytest.fixture(scope="session")
def libc():
    return c_import.loader.load(
        "libc.so.6",
        [
            "assert.h",
            # "complex.h", TODO: Not supported yet
            "ctype.h",
            "errno.h",
            "fenv.h",
            "float.h",
            "inttypes.h",
            "iso646.h",
            "limits.h",
            "locale.h",
            "math.h",
            "setjmp.h",
            "signal.h",
            "stdalign.h",
            "stdarg.h",
            # "stdatomic.h", TODO: Not supported yet
            "stdbool.h",
            "stddef.h",
            "stdint.h",
            "stdio.h",
            "stdlib.h",
            "stdnoreturn.h",
            "string.h",
            # "tgmath.h", TODO: Not supported yet
            "threads.h",
            "time.h",
            "uchar.h",
            "wchar.h",
            "wctype.h",
        ]
    )

def test_stream_globals(libc):
    assert libc.stdin
    assert libc.fileno(libc.stdin) == 0
    assert libc.fileno(libc.stdout) == 1
    assert libc.fileno(libc.stderr) == 2

def test_malloc(libc):
    @contextlib.contextmanager
    def malloc(size):
        new_address = libc.malloc(size)
        try:
            yield new_address
        finally:
            libc.free(new_address)

    with malloc(100) as address:
        libc.memset(address, 1, 100)


def test_numerics(libc):
    assert libc.abs(-1) == 1

    div_res = libc.div(34, 4)
    assert div_res.quot == 8
    assert div_res.rem == 2


def test_file_write(libc, tmp_path):
    f = tmp_path / "File.txt"
    fstream = libc.fopen(str(f).encode(), b"w+")
    text = ctypes.create_string_buffer(b"Hello world")
    libc.fwrite(text, len(text), 1, fstream)
    libc.fflush(fstream)
    libc.fclose(fstream)

    with open(f, "rb") as pyfile:
        assert pyfile.read() == text.raw

def test_number_conversions(libc):
    assert libc.atoi(b"-3") == -3
    assert libc.atol(b"-1048576") == -1048576
    assert libc.atoll(b"-1099511627776") == -1099511627776
    assert libc.atof(b"1.0003") == 1.0003

    endptr = ctypes.POINTER(ctypes.c_char)()
    assert libc.strtod(b"-1.324", ctypes.pointer(endptr)) == -1.324
    assert libc.strtof(b"-0.9", ctypes.pointer(endptr)) - -0.9 < 0.001
    assert libc.strtold(b"-1.324", ctypes.pointer(endptr)) == -1.324

    assert libc.strtol(b"1324", ctypes.pointer(endptr), 10) == 1324
    assert libc.strtoll(b"1324", ctypes.pointer(endptr), 10) == 1324

    assert libc.strtoul(b"1324", ctypes.pointer(endptr), 10) == 1324
    assert libc.strtoull(b"1324", ctypes.pointer(endptr), 10) == 1324

    # TODO: Check endptr


def test_scanf(libc):
    a = ctypes.c_uint()
    b = ctypes.c_char()
    c = ctypes.c_int()
    d = ctypes.c_float()

    scan_result = libc.sscanf(
        b"1 e -7 3.4",
        b"%u %c %d %f",
        ctypes.pointer(a),
        ctypes.pointer(b),
        ctypes.pointer(c),
        ctypes.pointer(d),
    )

    assert scan_result == 4
    assert a.value == 1
    assert b.value == b'e'
    assert c.value == -7
    assert abs(d.value - 3.4) < 0.01
