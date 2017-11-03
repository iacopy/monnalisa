#!/usr/bin/env bash

# Create html documentation from existing .rst files

set -e # exit immediately at first failed command (exit code != 0)
set -u # exit on undefined variables

# sphinx-build -b buildername sourcedir builddir
echo ============================================
echo Building html...
mkdir -p ./doc/_static  # necessary for sphinx-build
sphinx-build -c ./doc -b html ./doc/source ./doc/build/html -v

echo sphinx-build completed.
echo ============================================
