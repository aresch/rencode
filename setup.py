from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension(
        "rencode._rencode",
        sources=["rencode/_rencode.pyx"],
    )
]

setup(
    ext_modules=cythonize(
        extensions,
        compiler_directives={"language_level": "3", "binding": True},
    )
)

