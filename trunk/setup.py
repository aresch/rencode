#
# setup.py
#
# Copyright (C) 2010 Andrew Resch <andrewresch@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
#

from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules = [Extension("rencode", extra_compile_args=["-O3"], sources=["rencode.pyx"])]

setup(
  name = 'rencode',
  cmdclass = {'build_ext': build_ext},
  ext_modules = ext_modules
)
