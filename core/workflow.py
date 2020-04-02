from pathlib import Path
from typing import List, Dict, Union

from . import rdf, pythongen


def process_workflow(name: str, steps: List[Dict[str, Union[str, List[str]]]], target: Union[str, Path]) -> None:
    """
        Create a workflow stub including RDF definition and python stubs.
    :param name: Name of the workflpw
    :param steps: The individiual steps. These steps are defined as a list of Dicts that have the following keys:
        - name: Name of the step
        - description: Description of the step
        - inputs: List of str of the input parameterws
        - output: List of str of the output parameters
    :param target: Target directory
    :return:
    """
    workflow_dir = Path(target) / name
    workflow_dir.mkdir()
    pythongen.render_python_workflow(steps, workflow_dir)
    plex_file = workflow_dir / f'{name}.plex'
    plex_workflow = _create_plex_workflow(name, steps)
    plex_workflow.render(str(plex_file))


def _create_plex_workflow(name, steps):
    plex_workflow = rdf.PlexWorkflow(name)
    for step in steps:
        plex_workflow.add_step(step['name'], step['description'])

    return plex_workflow
