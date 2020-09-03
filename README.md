![Build Status](https://github.com/fair-workflows/FAIRWorkbench/workflows/Python%20application/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/fair-workflows/FAIRWorkbench/badge.svg?branch=master)](https://coveralls.io/github/fair-workflows/FAIRWorkbench?branch=master)

# FAIR Workbench

This repository contains some core software components for building the 'FAIR Workbench', as part of the FAIR is FAIR project. The workbench is intended to allow the description of workflows consisting of manual and computational steps using semantic technology, such as the ontology described in the publication:

_Celebi, R., Moreira, J. R., Hassan, A. A., Ayyar, S., Ridder, L., Kuhn, T., & Dumontier, M. (2019). Towards FAIR protocols and workflows: The OpenPREDICT case study._ [_arXiv:1911.09531._](https://arxiv.org/abs/1911.09531)

The goals of the project are to facilitate the construction of RDF descriptions of a variety of 'workflows', in the most general sense, that are commonly found in science (experimental procedures, ipython notebooks, manual procedures with computational analysis etc), and to allow validation and publication of the RDF, for example by means of nanopublications.


## ```fairworkflows``` python library
### Installation

From the root of the repo (directory containing ```setup.py```), run:

```
pip install .
```

### Description
The ```fairworkflows``` library has a number of modules to help with FAIRifying workflows:

* ```from fairworkflows import Nanopub```: This module provides a python classes and methods for searching, fetching and publishing to the nanopublication servers.
* ```from fairworkflows import FairStep```: This class is used to create, validate and publish rdf descriptions of an individual step (that can then be used in one or more workflows). Steps may be created from an rdflib graph, a function or by passing a URI to a nanopublication that describes a workflow step.
* ```from fairworkflows import FairWorkflow```: This class is used to create, validate and publish rdf descriptions of a general workflow. The workflow can be constructed from ```FairStep``` objects, or loaded from a nanopublication that describes a fair workflow. ```FairWorkflow``` objects are iterators, returning their constituent ```FairStep```s in an order specified by the step dependencies.

### Example
* See [test_plex_builder.ipynb](test_plex_builder.ipynb) for a current example of using the fairworkflows library to build a workflow using plex rdf

### Notes
The np script needs to be called to generate rsa keys in the `~/.nanopub` directory.

```shell script
fairworkflows/np mkkeys -a RSA
```

## How is the ```fairworkflows``` library expected to be used?
While this library could be used as a standalone tool to build/publish RDF workflows, it is intended more as a component to be used in a variety of other tools that seek to add FAIR elements to workflows. At present the library is used in the following tools:

* [NanopubJL](https://github.com/fair-workflows/NanopubJL): A Jupyter Lab extension that adds a widget for searching the nanopublication servers, and helps the user fetch desired nanopubs through injection of the necessary python code into a notebook cell.
* [FAIRWorkflowsExtension](https://github.com/fair-workflows/FAIRWorkflowsExtension): A Jupyter Lab extension that adds a widget for searching for previously published FairSteps or FairWorkflows. These can then be loaded into the notebook for modification or combination into new workflows.

It is expected that the library will soon interact with FAIR Data Points as well e.g. [fairdatapoint](https://github.com/NLeSC/fairdatapoint).

## Relation to existing workflow formats/engines (e.g. CWL, WDL, Snakemake etc)
This library is not intended to replace or compete with the hundreds of existing computational workflow formats, but rather to aid in RDF description and comparison of workflows in the most general sense of the term (including manual experiemental steps, notebooks, and so on). Steps in a FAIRWorkflow may very well be 'run this CWL workflow' or 'run this script', so such workflows are expected to sit more on a meta-level, describing the before-and-after of running one of these fully automated computational workflows as well.

