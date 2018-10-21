#
# setup.py
#
# Copyright (C) 2010 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2011 Pedro Algarvio <pedro@algarvio.me>
#
# Rencode is free software.
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

import sys
from distutils.errors import CCompilerError, DistutilsPlatformError

from setuptools import setup
from setuptools.extension import Extension

try:
    from Cython.Build import build_ext
    from Cython.Build import cythonize
except ImportError as ex:
    from setuptools.command.build_ext import build_ext
    cythonize = False

source_ext = ".pyx" if cythonize else ".c"

ext_modules = [
    Extension(
        "rencode._rencode",
        extra_compile_args=["-O3"],
        sources=["rencode/rencode" + source_ext],
    ),
]

if 'sdist' in sys.argv and not cythonize:
    exit('Error: sdist requires cython module to generate `.c` file.')

if cythonize:
    ext_modules = cythonize(ext_modules)

class optional_build_ext(build_ext):
    # This class allows C extension building to fail.
    def run(self):
        try:
            build_ext.run(self)
        except DistutilsPlatformError:
            _etype, e, _tb = sys.exc_info()
            self._unavailable(e)

    def build_extension(self, ext):
        try:
            build_ext.build_extension(self, ext)
            global _speedup_available
            _speedup_available = True
        except CCompilerError:
            _etype, e, _tb = sys.exc_info()
            self._unavailable(e)

    def _unavailable(self, exc):
        print('*' * 70)
        print("""WARNING:
The C extension could not be compiled, speedups will not be
available.""")
        print('*' * 70)
        print(exc)


setup(
  name="rencode",
  version="1.0.6",
  packages=["rencode"],
  description="Web safe object pickling/unpickling",
  long_description=open("README.md").read(),
  long_description_content_type="text/markdown",
  license='GPLv3',
  author="Andrew Resch",
  author_email="andrewresch@gmail.com",
  url="https://github.com/aresch/rencode",
  cmdclass={'build_ext': optional_build_ext},
  ext_modules=ext_modules,
  setup_requires=['setuptools', 'wheel'],
)
