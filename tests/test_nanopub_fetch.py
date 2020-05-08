from fairworkflows import Nanopub, FairData
import pytest

@pytest.mark.flaky(reruns=5)
def test_nanopub_search():
    """
        Check that Nanopub fetch is returning results for a few known nanopub URIs
    """

    known_nps = [
        'http://purl.org/np/RAFNR1VMQC0AUhjcX2yf94aXmG1uIhteGXpq12Of88l78'
    ]

    for np_uri in known_nps:
        np = Nanopub.fetch(np_uri)
        assert(isinstance(np, FairData))
        assert(np.source_uri == np_uri)
        assert(len(np.data) > 0)


