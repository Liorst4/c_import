import c_import
import ctypes
import pytest
import contextlib

@pytest.fixture
def libc():
    return c_import.loader.load("libc.so.6", ["stdlib.h",
                                              "stdio.h",
                                              "math.h",
                                              "string.h"])

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
