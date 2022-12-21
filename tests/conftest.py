import pytest
import rdflib
import requests

from fairworkflows.config import TESTS_RESOURCES

NANOPUB_SERVER = 'http://purl.org/np/'

skip_if_nanopub_server_unavailable = (
    pytest.mark.skipif(requests.get(NANOPUB_SERVER).status_code != 200,
                       reason='Nanopub server is unavailable'))

use_test_server=True

def read_rdf_test_resource(filename: str) -> rdflib.Graph():
    """
    Read RDF from a test resource
    """
    rdf = rdflib.ConjunctiveGraph()
    rdf.parse(str(TESTS_RESOURCES / filename), format='trig')
    return rdf
