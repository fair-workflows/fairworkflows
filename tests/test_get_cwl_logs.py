from config import TESTS_RESOURCES
from fairworkflows.ro_crate import ROCrate, parse_metadata
import shutil

SAMPLE_ROCRATE = TESTS_RESOURCES / 'test_crate.crate.zip'


def test_get_cwl_logs():

    print(SAMPLE_ROCRATE)
    crate = ROCrate(SAMPLE_ROCRATE)
    crate.run({'message': 'helloworld'})
