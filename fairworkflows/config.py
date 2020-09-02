from pathlib import Path

PACKAGE_DIR = Path(__file__).parent.absolute()
ROOT_DIR = PACKAGE_DIR.parent
TESTS_ROOT = ROOT_DIR/ 'tests'
TESTS_RESOURCES = TESTS_ROOT/ 'resources'

# Generated workflow directory names
PYTHON_DIR = 'scripts'
PLEX_DIR = 'plex'
