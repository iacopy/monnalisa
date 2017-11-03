#!/usr/bin/env bash
# Auto genera i file .rst di documentazione a partire dal codice python e dalle docstring.
# NB: Assume che ./doc/source/conf.py and ./doc/source/index.rst siano presenti

# E' quindi stato utile all'inizio per generare automaticamente una base di documentazione.

# La documentazione html viene generata a partire da questi .rst (oltre agli altri manualmente creati)
# tramite lo script apposito `doc_build_html.*`, che puo' essere lanciato nel CI.

set -e # exit immediately at first failed command (exit code != 0)
set -u # exit on undefined variables

echo Auto-generate modules documentation...
# Gli argomenti posizionali dal secondo in poi sono i path che *non* vuoi facciano
# parte della documentazione:
sphinx-apidoc --private -f -o ./doc/source ./src

echo
echo Aggiungere eventualmente la stringa \"modules\" al toctree di ./doc/source/index.rst,
echo per far elencare i moduli del progetto nell\'index.
