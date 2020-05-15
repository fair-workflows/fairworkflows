from pathlib import Path

PACKAGE_DIR = Path(__file__).parent.absolute()
ROOT_DIR = PACKAGE_DIR.parent
CLI_DIR = ROOT_DIR / 'cli'
TESTS_ROOT = ROOT_DIR/ 'tests'
TESTS_RESOURCES = TESTS_ROOT/ 'resources'

# Generated workflow directory names
PYTHON_DIR = 'scripts'
PLEX_DIR = 'plex'
CWL_DIR = 'cwl'
CWL_STEPS_DIR = f'{CWL_DIR}/steps'
CWL_WORKFLOW_DIR = f'{CWL_DIR}/workflow'

CWL_VERSION = 'v1.0'
