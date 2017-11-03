from distutils.core import setup
from Cython.Build import cythonize

setup(
  name = 'SimplestGA',
  ext_modules = cythonize("src/chars.pyx"),
)
