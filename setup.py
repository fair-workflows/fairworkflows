#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

# To update the package version number, edit demoflask/__version__.py
version = {}
with open(os.path.join(here, 'demoflask', '__version__.py')) as f:
    exec(f.read(), version)

with open('README.rst') as readme_file:
    readme = readme_file.read()

setup(
    name='demoflask',
    version=version['__version__'],
    description="Demo python library for annotating workflows",
    long_description=readme + '\n\n',
    author="Carlos Martinez",
    author_email='c.martinez@esciencecenter.nl',
    url='https://github.com/fair-workflows/demoflask',
    packages=[
        'demoflask',
    ],
    package_dir={'demoflask':
                 'demoflask'},
    include_package_data=True,
    license="Apache Software License 2.0",
    zip_safe=False,
    keywords='demoflask',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    install_requires=[
        'Flask'
    ],  # FIXME: add your package's dependencies to this list
    setup_requires=[
        # dependency for `python setup.py test`
        'pytest-runner',
        # dependencies for `python setup.py build_sphinx`
        'sphinx',
        'sphinx_rtd_theme',
        'recommonmark'
    ],
    tests_require=[
        'pytest',
        'pytest-cov',
        'pycodestyle',
    ],
    extras_require={
        'dev':  ['prospector[with_pyroma]', 'yapf', 'isort'],
    }
)
