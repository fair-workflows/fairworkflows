from pathlib import Path
from typing import List, Dict, Union
from fairworkflows.config import PYTHON_DIR, PLEX_DIR, CWL_DIR
from . import rdf, pythongen, cwl_cli


# TODO: Per input and output the type should be defined
def process_workflow(name: str, steps: List[Dict[str, Union[str, List[str]]]], target: Union[str, Path]) -> None:
    """
        Create a workflow stub including RDF definition and python stubs.
    :param name: Name of the workflpw
    :param steps: The individiual steps. These steps are defined as a list of Dicts that have the following keys:
        - name: Name of the step
        - description: Description of the step
        - input: List of str of the input parameterws
        - output: List of str of the output parameters
    :param target: Target directory
    :return:
    """
    workflow_dir = Path(target) / name

    workflow_dir.mkdir()

    scripts_dir = workflow_dir / PYTHON_DIR
    plex_dir = workflow_dir / PLEX_DIR
    cwl_dir = workflow_dir / CWL_DIR

    [d.mkdir() for d in [scripts_dir, plex_dir, cwl_dir]]

    pythongen.render_python_workflow(steps, workflow_dir)
    rdf.create_plex_workflow(name, steps, workflow_dir)
    cwl_cli.create_workflow(name, steps, workflow_dir)


def _create_plex_workflow(name, steps):
    plex_workflow = rdf.PlexWorkflow(name)
    for step in steps:
        plex_workflow.add_step(step['name'], step['description'])

    return plex_workflow
