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

import typing
import pathlib
import ctypes
import dataclasses

import clang
import clang.cindex


@dataclasses.dataclass(frozen=True)
class CInterface:
    types: dict[str, type]
    symbols: dict[str, object]
    enum_consts: dict[str, int]


QUALIFIERS_AND_SPECIFIERS = (
    "const",
    "volatile",
    "enum",
    "struct",
    "union",
    "restrict",
)

def remove_qualifiers_and_specifiers(name: str) -> str:
    words = name.split()
    filtered_words = filter(
        lambda x: x not in QUALIFIERS_AND_SPECIFIERS,
        words,
    )
    return ' '.join(filtered_words)


def unique_type_name(clang_type: clang.cindex.Type) -> str:
    '''Generate the name of the ctype type'''
    if clang_type.get_declaration().is_anonymous():
        return hex(hash(clang_type.get_canonical().spelling))

    return remove_qualifiers_and_specifiers(clang_type.spelling)


_CLANG_KIND_CTYPE_MAP = {
    clang.cindex.TypeKind.BOOL: ctypes.c_bool,
    clang.cindex.TypeKind.CHAR_U: ctypes.c_ubyte,
    clang.cindex.TypeKind.UCHAR: ctypes.c_ubyte,
    clang.cindex.TypeKind.USHORT: ctypes.c_ushort,
    clang.cindex.TypeKind.UINT: ctypes.c_uint,
    clang.cindex.TypeKind.ULONG: ctypes.c_ulong,
    clang.cindex.TypeKind.ULONGLONG: ctypes.c_ulonglong,
    clang.cindex.TypeKind.CHAR_S: ctypes.c_char,
    clang.cindex.TypeKind.SCHAR: ctypes.c_char,
    clang.cindex.TypeKind.WCHAR: ctypes.c_wchar,
    clang.cindex.TypeKind.SHORT: ctypes.c_short,
    clang.cindex.TypeKind.INT: ctypes.c_int,
    clang.cindex.TypeKind.ENUM: ctypes.c_int,
    clang.cindex.TypeKind.LONG: ctypes.c_long,
    clang.cindex.TypeKind.LONGLONG: ctypes.c_longlong,
    clang.cindex.TypeKind.FLOAT: ctypes.c_float,
    clang.cindex.TypeKind.DOUBLE: ctypes.c_double,
    clang.cindex.TypeKind.LONGDOUBLE: ctypes.c_longdouble,
    clang.cindex.TypeKind.VOID: None,
}

def get_type_or_create_variant(
        scope: CInterface,
        clang_type: clang.cindex.Type
) -> typing.Optional[type]:
    assert clang_type.spelling

    # TODO: Handle anonymous and opaque types

    if clang_type.kind in _CLANG_KIND_CTYPE_MAP:
        return _CLANG_KIND_CTYPE_MAP[clang_type.kind]

    if clang_type.kind == clang.cindex.TypeKind.INVALID:
        raise ValueError

    if clang_type.kind == clang.cindex.TypeKind.POINTER:
        return ctypes.POINTER(get_type_or_create_variant(scope, clang_type.get_pointee()))

    if clang_type.kind == clang.cindex.TypeKind.CONSTANTARRAY:
        return ctypes.ARRAY(
            get_type_or_create_variant(scope, clang_type.element_type),
            clang_type.element_count,
        )

    if clang_type.kind == clang.cindex.TypeKind.FUNCTIONPROTO:
        assert not clang_type.is_function_variadic()
        return ctypes.CFUNCTYPE(
            get_type_or_create_variant(scope, clang_type.get_result()),
            *map(
                lambda x: get_type_or_create_variant(scope, x),
                clang_type.argument_types(),
            ),
        )

    if clang_type.kind == clang.cindex.TypeKind.INCOMPLETEARRAY:
        return ctypes.POINTER(get_type_or_create_variant(scope, clang_type.element_type))

    if clang_type.kind in (
            clang.cindex.TypeKind.TYPEDEF,
            clang.cindex.TypeKind.ELABORATED,
    ):
        return get_type_or_create_variant(scope, clang_type.get_canonical())

    if clang_type.kind == clang.cindex.TypeKind.RECORD:
        type_id = unique_type_name(clang_type)
        if type_id not in scope.types:
            handle_struct_deceleration(scope, clang_type.get_declaration())
        return scope.types[type_id]

    raise NotImplementedError(clang_type.kind)


def handle_typedef_deceleration(scope: CInterface, cursor: clang.cindex.Cursor):
    assert cursor.kind == clang.cindex.CursorKind.TYPEDEF_DECL
    scope.types[cursor.spelling] = get_type_or_create_variant(scope, cursor.underlying_typedef_type)


def handle_type_deceleration_body(
        scope: CInterface,
        cursor: clang.cindex.Cursor,
        empty_type: type
):
    '''Handle variables, structs, unions, packed attrs, etc... in a ctype.'''

    fields_to_add = []
    pack_value = None
    anon_types_to_add = []

    for child in cursor.get_children():
        if child.kind == clang.cindex.CursorKind.FIELD_DECL:
            field = [child.spelling, get_type_or_create_variant(scope, child.type)]
            if child.is_bitfield():
                field.append(child.get_bitfield_width())

            # If its bounded to a field, than its not suppose to be in _anonymous_
            field_type_name = field[1].__name__
            if field_type_name in anon_types_to_add:
                anon_types_to_add.remove(field_type_name)

            assert(field[1] != None)
            fields_to_add.append(tuple(field))

        elif child.kind == clang.cindex.CursorKind.PACKED_ATTR:
            pack_value = 1

        elif child.kind in (
                clang.cindex.CursorKind.STRUCT_DECL,
                clang.cindex.CursorKind.UNION_DECL
        ):
            handler = handle_struct_deceleration \
                if child.kind == clang.cindex.CursorKind.STRUCT_DECL \
                   else handle_union_deceleration
            nested_ctype_name = unique_type_name(child.type)
            if nested_ctype_name not in scope.types:
                nested_ctype = handler(scope, child)
                anon_types_to_add.append(nested_ctype_name)
                assert nested_ctype is not None
                fields_to_add.append((nested_ctype_name, nested_ctype))

        else:
            raise NotImplementedError(child.kind)

    if pack_value is not None:
        empty_type._pack_ = pack_value

    if len(anon_types_to_add) != 0:
        for t in map(lambda x: scope.types[x], anon_types_to_add):
            if not hasattr(t, '_fields_'):
                setattr(t, '_fields_', [])
        empty_type._anonymous_ = anon_types_to_add

    if len(fields_to_add) != 0:
        empty_type._fields_ = fields_to_add


def add_type_with_fields(
        expected_cursor_kind: clang.cindex.CursorKind,
        ctypes_type: type,
        scope: CInterface,
        cursor: clang.cindex.Cursor
) -> type:
    assert cursor.kind == expected_cursor_kind
    type_name = unique_type_name(cursor.type)
    ctype = None
    if type_name in scope.types:
        # Get a forward decleration reference
        # to expand.
        # TODO: Verifiy its a forward deceleration
        ctype = scope.types[type_name]
    else:
        # Create a new ctypes class
        ctype = type(type_name, (ctypes_type, ), dict())

    assert " " not in type_name
    scope.types[type_name] = ctype  # Add refrence to table
    handle_type_deceleration_body(scope, cursor, ctype)
    return ctype


def handle_struct_deceleration(
        scope: CInterface,
        cursor: clang.cindex.Cursor
) -> type:
    return add_type_with_fields(
        clang.cindex.CursorKind.STRUCT_DECL,
        ctypes.Structure,
        scope,
        cursor
    )


def handle_union_deceleration(
        scope: CInterface,
        cursor: clang.cindex.Cursor
) -> type:
    return add_type_with_fields(
        clang.cindex.CursorKind.UNION_DECL,
        ctypes.Union,
        scope,
        cursor
    )


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
