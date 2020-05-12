from config import TESTS_RESOURCES
from fairworkflows.ro_crate import ROCrate, parse_metadata
import shutil

SAMPLE_ROCRATE = TESTS_RESOURCES / 'test_crate.crate.zip'

def test_run_cwl_from_rocrate():

    crate = ROCrate(SAMPLE_ROCRATE)
    crate.run({'message': 'helloworld'})

    assert True
