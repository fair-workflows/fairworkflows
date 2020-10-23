import pytest
import requests

NANOPUB_SERVER = 'http://purl.org/np/'

skip_if_nanopub_server_unavailable = (
    pytest.mark.skipif(requests.get(NANOPUB_SERVER).status_code != 200,
                       reason='Nanopub server is unavailable'))

