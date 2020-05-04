"""
Project module contains all functions related to loading project files and metadata.
"""
from collections import defaultdict
from pathlib import Path
from typing import Union, Dict

from rdflib.plugins.sparql.processor import SPARQLResult

from config import PLEX_DIR, PYTHON_DIR
from . import rdf


def _load_workflow(project_path: Union[str, Path]):
    """
    Loads "generic" implementation of the workflow. Right now this representation is based on the cwl data.

    :param project_path:
    :return:
    """
    project_path = Path(project_path)
    workflow_path = project_path / PLEX_DIR

    # Assuming the workflow directory has only one file
    workflow_file = next(workflow_path.iterdir())
    workflow_file = str(workflow_file)

    return rdf.load_workflow(workflow_file)


def get_step_code(project_path, step_name):
    project_path = Path(project_path)
    steps_path = project_path / PYTHON_DIR

    step_file = steps_path / f'{step_name}.py'

    return step_file.read_text()


def get_steps(project_path: str):
    """
    Get description of the steps in the workflow. For now these descriptions are based on the RDF description.
    :param project_path:
    :return:
    """
    wf = _load_workflow(project_path)

    # TODO: Probably not the most efficient way
    step_triples = wf.query('''SELECT ?s ?p ?o
                                WHERE
                                {
                                    ?s a p-plan:Step .
                                    ?s ?p ?o .
                                }''')

    return _sparqlresult_to_step_dict(step_triples)


def _sparqlresult_to_step_dict(result: SPARQLResult) -> Dict[str, any]:
    step_dict = defaultdict(dict)

    # TODO: If needed there is a lot to be optimized here
    for step_ref, predicate, object in result:
        step_name = _step_uri_to_name(step_ref)
        step_dict[step_name].update({predicate: object})
        step_dict[step_name].update({'uri': step_ref})

    return step_dict


def _step_uri_to_name(uri: str) -> str:
    return uri.split('/')[-1]
