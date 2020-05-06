import os
from pathlib import Path

ROOT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
CLI_DIR = ROOT_DIR / 'cli'
CORE_DIR = ROOT_DIR / 'core'

# Generated workflow directory names
PYTHON_DIR = 'scripts'
PLEX_DIR = 'plex'
CWL_DIR = 'cwl'
CWL_STEPS_DIR = f'{CWL_DIR}/steps'
CWL_WORKFLOW_DIR = f'{CWL_DIR}/workflow'

CWL_VERSION = 'v1.0'

# Location of nanopub tool
ROOT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
NANOPUB_SCRIPT = str(ROOT_DIR/'np')
