#!/bin/bash -i

python3 -m pip install . || exit 1
jupyter-notebook test.ipynb
