import pytest
import requests

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
        assert(step is not None)
        assert(step.validate())
        assert(step.is_pplan_step())
        assert(step.description() is not None)
        assert(step.is_manual_task() is True)
        assert(step.is_script_task() is False)
