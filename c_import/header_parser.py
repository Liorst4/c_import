# Copyright (C) 2022  Lior Stern
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

import typing
import pathlib
import ctypes

import clang

from c_import._header_parser import *


def handle_enum_deceleration(scope: CInterface, cursor: clang.cindex.Cursor):
    assert cursor.kind == clang.cindex.CursorKind.ENUM_DECL
    enum_name = unique_type_name(cursor.type)
    scope.types[enum_name] = ctypes.c_int
    for c in cursor.get_children():
        assert c.kind == clang.cindex.CursorKind.ENUM_CONSTANT_DECL
        scope.enum_consts[c.spelling] = c.enum_value


def handle_var_deceleration(scope: CInterface, cursor: clang.cindex.Cursor):
    assert cursor.kind == clang.cindex.CursorKind.VAR_DECL
    var_type = get_type_or_create_variant(scope, cursor.type)
    scope.symbols[cursor.spelling] = var_type


def handle_function_deceleration(
        scope: CInterface,
        cursor: clang.cindex.Cursor
):
    # TODO: Handle stdcall
    assert cursor.kind == clang.cindex.CursorKind.FUNCTION_DECL
    function = ctypes.CFUNCTYPE(
        get_type_or_create_variant(scope, cursor.result_type),
        *map(
            lambda x:get_type_or_create_variant(scope, x.type),
            cursor.get_arguments(),
        )
    )
    scope.symbols[cursor.spelling] = function


_DECELERATION_HANDLER = {
    clang.cindex.CursorKind.TYPEDEF_DECL: handle_typedef_deceleration,
    clang.cindex.CursorKind.STRUCT_DECL: handle_struct_deceleration,
    clang.cindex.CursorKind.UNION_DECL: handle_union_deceleration,
    clang.cindex.CursorKind.ENUM_DECL: handle_enum_deceleration,
    clang.cindex.CursorKind.VAR_DECL: handle_var_deceleration,
    clang.cindex.CursorKind.FUNCTION_DECL: handle_function_deceleration,
}

def handle_deceleration(scope: CInterface, cursor: clang.cindex.Cursor):
    assert cursor.kind.is_declaration()
    if cursor.kind not in _DECELERATION_HANDLER:
        raise NotImplementedError(cursor.kind)
    _DECELERATION_HANDLER[cursor.kind](scope, cursor)


def handle_translation_unit(scope: CInterface, cursor: clang.cindex.Cursor):
    assert cursor.kind == clang.cindex.CursorKind.TRANSLATION_UNIT
    for child in cursor.get_children():
        handle_deceleration(scope, child)


def parse_header(header: pathlib.Path) -> CInterface:
    scope = CInterface(types=dict(), symbols=dict(), enum_consts=dict())
    handle_translation_unit(
        scope,
        clang.cindex.Index.create().parse(header).cursor
    )
    assert "" not in scope.types.keys()
    return scope
