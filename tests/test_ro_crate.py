from config import TESTS_RESOURCES
from fairworkflows.ro_crate import ROCrate, parse_metadata
import shutil

SAMPLE_METADATA = TESTS_RESOURCES / 'ro-crate-metadata.jsonld'


def test_jsonld_parses_as_json():
    metadata = parse_metadata(SAMPLE_METADATA)

    assert '@graph' in metadata.keys()


def test_rocrate_finds_cwl_file(tmp_path):
    _mock_ro_crate(tmp_path)

    crate = ROCrate(tmp_path)

    assert crate.cwltool.name == 'TranscriptsAnnotation-wf.cwl'


def _mock_ro_crate(tmp_dir):
    shutil.copy(SAMPLE_METADATA, tmp_dir)
