import os
from pathlib import Path

ROOT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
CLI_DIR = ROOT_DIR / 'cli'
CORE_DIR = ROOT_DIR / 'fairworkflows'
TESTS_ROOT = ROOT_DIR/ 'tests'
TESTS_RESOURCES = TESTS_ROOT/ 'resources'

# Generated workflow directory names
PYTHON_DIR = 'scripts'
PLEX_DIR = 'plex'
CWL_DIR = 'cwl'
CWL_STEPS_DIR = f'{CWL_DIR}/steps'
CWL_WORKFLOW_DIR = f'{CWL_DIR}/workflow'

CWL_VERSION = 'v1.0'
