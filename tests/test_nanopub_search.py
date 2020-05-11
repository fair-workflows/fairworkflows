from fairworkflows import Nanopub
import pytest

@pytest.mark.flaky(reruns=5)
def test_nanopub_search():
    """
        Check that Nanopub search is returning results for a few common search terms
    """

    searches = ['fair', 'heart']

    for search in searches:
        results = Nanopub.search(search)
        assert(len(results) > 0)
