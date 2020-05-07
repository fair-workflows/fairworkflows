from config import TESTS_RESOURCES
from fairworkflows import ro_crate

SAMPLE_METADATA = TESTS_RESOURCES / 'ro-crate-metadata.jsonld'


def test_jsonld_parses_as_json():
    metadata = ro_crate.parse_metadata(SAMPLE_METADATA)

    assert '@graph' in metadata.keys()
