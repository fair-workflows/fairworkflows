#!/usr/bin/env python

from setuptools import setup, find_packages
import distutils

import codecs
import os.path

def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()

def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")

setup(name='fairworkflows',
    version=get_version('fairworkflows/_version.py'),
    description='FAIRWorkflows python library',
    author='Robin Richardson',
    author_email='r.richardson@esciencecenter.nl',
    url='https://example.org',
    install_requires=open("requirements.txt", "r").readlines(),
    packages=find_packages(),
    include_package_data=True
)
