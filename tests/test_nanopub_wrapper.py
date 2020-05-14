import pytest

from fairworkflows import nanopub_wrapper
from fairworkflows.config import TESTS_RESOURCES
from pathlib import Path
import shutil

NANOPUB_SAMPLE_SIGNED = TESTS_RESOURCES / 'nanopub_sample_signed.trig'
NANOPUB_SAMPLE_UNSIGNED = TESTS_RESOURCES / 'nanopub_sample_unsigned.trig'


def test_extract_nanopub_url_from_namespace():
    url = nanopub_wrapper.extract_nanopub_url(NANOPUB_SAMPLE_SIGNED)

    target_url = 'http://purl.org/np/RAzPytdERsBd378zHGvwgRbat1MCiS7QrxNrPxe9yDu6E'
    assert target_url == url


def test_sign_nanopub_creates_file(tmp_path):
    # Work in temporary dir so resulting files do not end up in repo
    temp_unsigned_file = tmp_path / 'unsigned.trig'
    shutil.copy(NANOPUB_SAMPLE_UNSIGNED, temp_unsigned_file)

    signed_file = nanopub_wrapper.sign(unsigned_file=temp_unsigned_file)

    assert Path(signed_file).exists()


def test_sign_fails_on_invalid_nanopub(tmp_path):
    invalid_file = tmp_path / 'invalid.trig'
    invalid_file.write_text('this file is invalid')

    with pytest.raises(Exception):
        nanopub_wrapper.sign(invalid_file)
