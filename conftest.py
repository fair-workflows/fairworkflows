import pytest
import requests

NANOPUB_SERVER = 'http://purl.org/np/'


def nanopub_server_available():
    response = requests.get(NANOPUB_SERVER)
    return response.status_code == 200


skip_if_nanopub_server_unavailable = (
    pytest.mark.skipif(not nanopub_server_available(),
                       reason='Nanopub server is unavailable'))

