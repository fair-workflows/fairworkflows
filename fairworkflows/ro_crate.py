import json
from pathlib import Path
from typing import Union, Dict, List

from . import cwl

METADATA_FILE = 'ro-crate-metadata.jsonld'

CONTEXT_KEY = '@context'


class ROCrate:

    def __init__(self, path: Union[str, Path]):
        self.path = Path(path)
        self.metadata_path = self.path / METADATA_FILE
        self.metadata = self.metadata_path.read_text()
        self.metadata_graph = parse_metadata(self.metadata_path)
        self.cwltool = self.path/_get_cwltool_path(self.metadata_graph)

    def run(self, inputs):
        cwl.run_workflow(wf_path=self.cwltool, inputs=inputs, base_dir=self.path)

    def __str__(self) -> str:
        return f'ROCrate(\n' \
               f'        path={self.path}' \
               f'        metadata_graph={self.metadata_graph}\n' \
               f'        metadata={self.metadata}\n' \
               f'       )'


def parse_metadata(path: Path) ->Dict[str, any]:
    """
    Parse RO-crate metadata as a regular json file.

    :param path:
    :return:
    """
    with path.open('r') as f:
        return json.load(f)


def _get_cwltool_path(metadata: Dict[str, any]) -> str:
    main_metadata = filter(lambda d: d['@id'] == './', metadata['@graph'])
    main_metadata = list(main_metadata)[0]

    return main_metadata['mainEntity']['@id']
