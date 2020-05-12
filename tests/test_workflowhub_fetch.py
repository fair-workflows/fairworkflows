from fairworkflows import Workflowhub, FairData, ROCrate
import pytest

@pytest.mark.flaky(reruns=5)
def test_workflowhub_search():
    """
        Check that Workflowhub fetch is returning results for a few known URLs.
        Check that the returned object is of type FairData, that it has the expected
        source_uri, and that it has non-zero data.
    """

    known_urls = [
        'https://dev.workflowhub.eu/workflows/52/download',
        'https://dev.workflowhub.eu/workflows/49/download',
        'https://dev.workflowhub.eu/workflows/48/download'
    ]

    for wf_url in known_urls:
        wf = Workflowhub.fetch(wf_url)
        assert(isinstance(wf, FairData))
        assert(wf.source_uri == wf_url)
        assert(isinstance(wf.data, ROCrate))


