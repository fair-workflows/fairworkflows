from fairworkflows import Nanopub, FairData
import pytest

@pytest.mark.flaky(max_runs=10)
def test_nanopub_search():
    """
        Check that Nanopub search is returning results for a few common search terms
    """

    searches = ['fair', 'heart']

    for search in searches:
        results = Nanopub.search(search)
        assert(len(results) > 0)


@pytest.mark.flaky(max_runs=10)
def test_nanopub_search():
    """
        Check that Nanopub fetch is returning results for a few known nanopub URIs.
        Check that the returned object is of type FairData, that it has the expected
        source_uri, and that it has non-zero data.
    """

    known_nps = [
        'http://purl.org/np/RAFNR1VMQC0AUhjcX2yf94aXmG1uIhteGXpq12Of88l78',
        'http://purl.org/np/RAePO1Fi2Wp1ARk2XfOnTTwtTkAX1FBU3XuCwq7ng0jIo',
        'http://purl.org/np/RA48Iprh_kQvb602TR0ammkR6LQsYHZ8pyZqZTPQIl17s'
    ]

    for np_uri in known_nps:
        np = Nanopub.fetch(np_uri)
        assert(isinstance(np, FairData))
        assert(np.source_uri == np_uri)
        assert(len(np.data) > 0)


