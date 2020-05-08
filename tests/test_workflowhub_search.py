from fairworkflows import Workflowhub
import pytest

@pytest.mark.flaky(reruns=5)
def test_workflowhub_search():
    """
        Check that Workflowhub search is returning results for a few common search terms
    """

    searches = ['covid', 'workflow']

    for search in searches:
        results = Workflowhub.search(search)
        assert(len(results) > 0)
