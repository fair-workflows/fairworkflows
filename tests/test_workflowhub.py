from fairworkflows import Workflowhub, FairData, ROCrate
import pytest

@pytest.mark.flaky(max_runs=10)
def test_workflowhub_search():
    """
        Check that Workflowhub search is returning results for a few common search terms
    """

    searches = ['covid', 'workflow']

    for search in searches:
        results = Workflowhub.search(search)
        assert(len(results) > 0)


@pytest.mark.flaky(max_runs=10)
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
        assert (isinstance(wf, FairData))
        assert (wf.source_uri == wf_url)
        assert (isinstance(wf.data, ROCrate))
