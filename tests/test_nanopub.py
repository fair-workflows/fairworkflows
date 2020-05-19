import pytest
import requests

from fairworkflows import Nanopub, FairData

DEFAULT_FORMAT = '.trig'
BAD_GATEWAY = 502
NANOPUB_SERVER = 'http://purl.org/np/'
SERVER_UNAVAILABLE = 'Nanopub server is unavailable'


def nanopub_server_unavailable():
    response = requests.get(NANOPUB_SERVER)

    return response.status_code == BAD_GATEWAY


@pytest.mark.flaky(max_runs=10)
@pytest.mark.skipif(nanopub_server_unavailable(), reason=SERVER_UNAVAILABLE)
def test_nanopub_search():
    """
        Check that Nanopub search is returning results for a few common search terms
    """

    searches = ['fair', 'heart']

    for search in searches:
        results = Nanopub.search_text(search)
        assert(len(results) > 0)


@pytest.mark.flaky(max_runs=10)
@pytest.mark.skipif(nanopub_server_unavailable(), reason=SERVER_UNAVAILABLE)
def test_nanopub_fetch():
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
        assert (isinstance(np, FairData))
        assert (np.source_uri == np_uri)
        assert (len(np.data) > 0)
