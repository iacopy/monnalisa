#!/usr/bin/env bash

# Script di "bootstrap" per creare la documentazione con sphinx.
# Genera ./doc2/source/conf.py, ./doc2/source/index.rst e Makefile

# Lo script non deve essere eseguito ogni volta, e' stato utile all'inizio
# per avere conf.py e index.rst che poi vengono committati e modificati
# manualmente quando serve.

echo sphinx-quickstart...
sphinx-quickstart -p SimpleGA -q -a Iacopo -v 0.1 -r 0.1.0 -l en --ext-autodoc --sep ./doc
# sposto il conf nella root della doc
mv ./doc/source/conf.py ./doc
echo
echo NB: Aggiungere la riga \''sys.path.insert(0, os.path.abspath("../src"))'\' a \''./doc/conf.py'\'.
