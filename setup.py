#!/usr/bin/env python

import codecs
import os.path

from setuptools import setup


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


setup(
    name='fairworkflows',
    version=get_version('fairworkflows/_version.py'),
    description='FAIRWorkflows python library',
    long_description=open("README.md").read(),
    long_description_content_type='text/markdown',
    author='Robin Richardson, Djura Smits, Sven van den Burg',
    author_email='r.richardson@esciencecenter.nl',
    url='https://github.com/fair-workflows/fairworkflows/',
    install_requires=open("requirements.txt").readlines(),
    packages=['fairworkflows'],
    extras_require={
        'dev': open('requirements_dev.txt').readlines()
    },
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent"
    ],
    python_requires='>=3.6'
)
