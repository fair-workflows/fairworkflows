from fairworkflows import nanopub_wrapper
from fairworkflows.config import TESTS_RESOURCES

NANOPUB_SAMPLE = TESTS_RESOURCES / 'nanopub_sample.trig'

def test_extract_nanopub_url_from_namespace():
    url = nanopub_wrapper.extract_nanopub_url(NANOPUB_SAMPLE)

    target_url = 'http://purl.org/np/RAzPytdERsBd378zHGvwgRbat1MCiS7QrxNrPxe9yDu6E'
    assert target_url == url
