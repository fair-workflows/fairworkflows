"""
Project module contains all functions related to loading project files and metadata.
"""

from pathlib import Path
from typing import Union, Dict, Iterable
from config import CWL_WORKFLOW_DIR, CWL_STEPS_DIR

import yaml


def _load_workflow(project_path: Union[str, Path]):
    """
    Loads "generic" implementation of the workflow. Right now this representation is based on the cwl data.

    :param project_path:
    :return:
    """
    project_path = Path(project_path)
    workflow_path = project_path / CWL_WORKFLOW_DIR

    # Assuming the workflow directory has only one file
    workflow_file = next(workflow_path.iterdir())
    workflow_file = str(workflow_file)

    with open(workflow_file, 'r') as f:
        wf = yaml.load(f)

    return wf


def get_steps(project_path: str) -> Dict[str, any]:
    wf = _load_workflow(project_path)
    return wf['steps']
