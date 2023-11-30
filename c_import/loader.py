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

import ctypes
import _ctypes
import typing
import pathlib
import tempfile

import c_import.header_parser
from c_import._loader import *

# TODO: Better name
class CDLLX(ctypes.CDLL):
    def __init__(
            self,
            library,
            headers: typing.Sequence[pathlib.Path],
            cpp_command: typing.Optional[str]=None,
            cpp_flags: typing.Optional[str]=None
    ):
        super().__init__(library)
        with tempfile.NamedTemporaryFile(
                mode='w',
                encoding='utf-8',
                suffix='.h'
        ) as combined_header:
            combined_header.write(preprocess_headers(
                headers,
                cpp_command,
                cpp_flags
            ))
            combined_header.flush()
            self._interface = c_import.header_parser.parse_header(combined_header.name)

    def __getitem__(self, item):
        if item in self._interface.symbols:
            ctype = self._interface.symbols.get(item)
            if issubclass(ctype, _ctypes.CFuncPtr):
                return ctype((item, self))
            else:
                return ctype.in_dll(self, item)

        if item in self._interface.enum_consts:
            return self._interface.enum_consts.get(item)

        if item in self._interface.types:
            return self._interface.types.get(item)

        raise KeyError

load = CDLLX
