import pytest
import requests
from unittest.mock import patch
import rdflib

from fairworkflows import FairStep

BAD_GATEWAY = 502
NANOPUB_SERVER = 'http://purl.org/np/'
SERVER_UNAVAILABLE = 'Nanopub server is unavailable'

def nanopub_server_unavailable():
    response = requests.get(NANOPUB_SERVER)

    return response.status_code == BAD_GATEWAY


@pytest.mark.flaky(max_runs=10)
@pytest.mark.skipif(nanopub_server_unavailable(), reason=SERVER_UNAVAILABLE)
def test_fairstep_from_nanopub():
    """
        Check that we can load a FairStep from known nanopub URIs for manual steps,
        that validation works, etc
    """

    nanopub_uris = [
        'http://purl.org/np/RACLlhNijmCk4AX_2PuoBPHKfY1T6jieGaUPVFv-fWCAg#step',
        'http://purl.org/np/RANBLu3UN2ngnjY5Hzrn7S5GpqFdz8_BBy92bDlt991X4#step',
        'http://purl.org/np/RA5D8NzM2OXPZAWNlADQ8hZdVu1k0HnmVmgl20apjhU8M#step'
    ]

    for uri in nanopub_uris:
        step = FairStep(uri=uri, from_nanopub=True)
        assert step is not None
        step.validate()
        assert step.is_pplan_step
        assert step.description is not None
        assert step.is_manual_task
        assert not step.is_script_task


@pytest.mark.flaky(max_runs=10)
@pytest.mark.skipif(nanopub_server_unavailable(), reason=SERVER_UNAVAILABLE)
def test_fairstep_from_nanopub_without_fragment():
    """
        Check that we can load a FairStep from known nanopub URIs also
        in cases where the full step URI is not used (i.e. missing a fragment).
        In other words, only the nanopub URI is given, but not the URI of the
        step itself within that nanopub.
    """

    nanopub_uris = [
        'http://purl.org/np/RACLlhNijmCk4AX_2PuoBPHKfY1T6jieGaUPVFv-fWCAg',
        'http://purl.org/np/RANBLu3UN2ngnjY5Hzrn7S5GpqFdz8_BBy92bDlt991X4',
        'http://purl.org/np/RA5D8NzM2OXPZAWNlADQ8hZdVu1k0HnmVmgl20apjhU8M'
    ]

    for uri in nanopub_uris:
        step = FairStep(uri=uri, from_nanopub=True)
        assert step is not None
        step.validate()
        assert step.is_pplan_step
        assert step.description is not None
        assert step.is_manual_task
        assert not step.is_script_task


def test_fairstep_from_function():
    def add(a: int, b: int):
        """
        Computational step adding two ints together.
        """
        return a + b

    step = FairStep(func=add)

    assert step is not None
    step.validate()
    assert step.is_pplan_step
    assert step.description is not None
    assert not step.is_manual_task
    assert step.is_script_task

    assert step.__str__() is not None
    assert len(step.__str__()) > 0
    assert step.rdf is not None


def test_validation():
    step = FairStep(uri='http://www.example.org/step')
    with pytest.raises(AssertionError):
        step.validate()


@pytest.mark.flaky(max_runs=10)
@pytest.mark.skipif(nanopub_server_unavailable(), reason=SERVER_UNAVAILABLE)
@patch('fairworkflows.nanopub_wrapper.publish')
def test_modification_and_republishing(nanopub_wrapper_publish_mock):

    preheat_oven = FairStep(uri='http://purl.org/np/RACLlhNijmCk4AX_2PuoBPHKfY1T6jieGaUPVFv-fWCAg#step', from_nanopub=True)
    assert preheat_oven is not None
    assert not preheat_oven.is_modified
    original_uri = preheat_oven.uri
    preheat_oven.publish_as_nanopub()
    assert preheat_oven.uri == original_uri

    # Now modify the step description
    preheat_oven.description =  'Preheat an oven to 200 degrees C.'
    assert preheat_oven.is_modified is True
    preheat_oven.publish_as_nanopub()
    assert nanopub_wrapper_publish_mock.called
    assert preheat_oven.uri != original_uri
    assert preheat_oven.is_modified is False


