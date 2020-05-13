import json
from pathlib import Path
from typing import Union, Dict, List
import zipfile
import tempfile

from . import cwl

METADATA_FILE = 'ro-crate-metadata.jsonld'
CONTEXT_KEY = '@context'


class ROCrate:
    """
    Class that holds all necessary data on cwl RO crates.

    """

    def __init__(self, path_to_zip: Union[str, Path]):
        """
        Find the mandatory metadata file in path and infer the path to the main cwltool.

        :param path:
        """

        temp_dir = tempfile.mkdtemp()
        with zipfile.ZipFile(path_to_zip, 'r') as z:
            z.extractall(path=temp_dir)

        self.path = Path(temp_dir)
        self.metadata_path = self.path / METADATA_FILE
        self.metadata = self.metadata_path.read_text()
        self.metadata_graph = parse_metadata(self.metadata_path)
        self.cwltool = self.path/_get_cwltool_path(self.metadata_graph)

        self.run_log = ''

    def run(self, inputs: Dict[str, any]):
        """
        Run the main cwltool of this RO crate.

        :param inputs:
        :return:
        """
        _, self.run_log = cwl.run_workflow(wf_path=self.cwltool, inputs=inputs, base_dir=self.path)
        return self.run_log

    def __str__(self) -> str:
        return f'ROCrate(\n' \
               f'        path={self.path}' \
               f'        metadata_graph={self.metadata_graph}\n' \
               f'        metadata={self.metadata}\n' \
               f'       )'


def parse_metadata(path: Path) ->Dict[str, any]:
    """
    Parse RO-crate metadata as a regular json file.

    json-ld libraries like the jsonld-rdflib are still quite immature and have a lot of issues.

    :param path:
    :return:
    """
    with path.open('r') as f:
        return json.load(f)


def _get_cwltool_path(metadata: Dict[str, any]) -> str:
    main_metadata = filter(lambda d: d['@id'] == './', metadata['@graph'])
    main_metadata = list(main_metadata)[0]

    return main_metadata['mainEntity']['@id']
