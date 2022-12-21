# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2022-12-15

### Added

* Migrate to use `pyproject.toml` with a `hatch` build backend
* Add pre-commit and a `.pre-commit-config.yaml` to make sure the files are properly formatted (similar to the nanopub package setup).

### Modified

* Update the `nanopub` dependency to 2.0.0 (no need for java anymore) and make the changes required.
* Update rdflib dependency to v6+

### Removed

* Configuration files in the root folder of the repository have been removed, their configuration being now moved in the pyproject.toml: `setup.py`, ` MANIFEST.in `, `pytest.ini `, `requirements.txt`, `requirements_dev.txt`, `.flake8`, `.coveragerc`

## [0.3.0] - 2021-06-25

### Added
* Added CHANGELOG.md, CODE_OF_CONDUCT.md and CONTRIBUTING.md

### Changed
* Upgrade to nanopub v1.2.7 (among other things, to fix click bug)
