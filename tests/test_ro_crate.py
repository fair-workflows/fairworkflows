from fairworkflows.config import TESTS_RESOURCES
from fairworkflows.ro_crate import ROCrate, parse_metadata

SAMPLE_METADATA = TESTS_RESOURCES / 'ro-crate-metadata.jsonld'
SAMPLE_ROCRATE = TESTS_RESOURCES / 'test_crate.crate.zip'

def test_jsonld_parses_as_json():
    metadata = parse_metadata(SAMPLE_METADATA)

    assert '@graph' in metadata.keys()


def test_rocrate_finds_cwl_file(tmp_path):

    crate = ROCrate(SAMPLE_ROCRATE)

    assert crate.cwltool.name == 'test_workflow.cwl'
