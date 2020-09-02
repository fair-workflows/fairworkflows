![Build Status](https://github.com/fair-workflows/FAIRWorkbench/workflows/Python%20application/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/fair-workflows/FAIRWorkbench/badge.svg?branch=master)](https://coveralls.io/github/fair-workflows/FAIRWorkbench?branch=master)

# FAIRWorkbench
Modules for implementation of the FAIR Workbench.

# Prerequisites
The np scripts needs to be called to generate rsa keys in the `~/.nanopub` directory.

```shell script
fairworkflows/np mkkeys -a RSA
```

# ```fairworkflows``` python library
## Installation

From the root of the repo (directory containing ```setup.py```), run:

```
pip install .
```

## Usage
* See [test_plex_builder.ipynb](test_plex_builder.ipynb) for a current example of using the fairworkflows library to build a workflow using plex rdf

