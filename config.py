import os
from pathlib import Path

ROOT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
CLI_DIR = ROOT_DIR / 'cli'
CORE_DIR = ROOT_DIR / 'core'

CWL_VERSION = 'v1.0'

NANOPUB_SCRIPT = str(ROOT_DIR/'np')
