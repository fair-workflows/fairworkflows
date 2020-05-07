from pathlib import Path
from typing import Union, Dict
from rdflib import Graph
from . import cwl
import json

METADATA_FILE = 'ro-crate-metadata.jsonld'

CONTEXT_KEY = '@context'


class ROCrate:

    def __init__(self, path: Union[str, Path]):
        self.path = Path(path)
        self.metadata_path = self.path / METADATA_FILE
        self.metadata = self.metadata_path.read_text()
        self.metadata_graph = parse_metadata(self.metadata_path)

    def run(self, inputs):
        cwl.run_workflow(wf_path=self.path, inputs=inputs)

    def __str__(self) -> str:
        return f'''ROCrate(
                            path={self.path}
                            metadata_graph={self.metadata_graph}
                            metadata={self.metadata}
                          )'''


def parse_metadata(path: Path) -> Dict[str, any]:
    """
    Parse RO-crate metadata as a regular json file.

    :param path:
    :return:
    """
    with path.open('r') as f:
        return json.load(f)


#
# def _get_context(path):
#     with path.open('r') as f:
#         j = json.load(f)
#
#         return j[CONTEXT_KEY]


def _get_cwltool_path(graph: Graph) -> Path:
    graph.query('?file type wirjfl')
