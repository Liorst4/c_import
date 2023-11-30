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

import pathlib
import clang

from c_import._header_parser import *


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
