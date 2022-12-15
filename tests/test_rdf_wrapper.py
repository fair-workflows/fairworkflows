import warnings

import pytest
import rdflib

from conftest import use_test_server
from fairworkflows.rdf_wrapper import RdfWrapper


class TestRdfWrapper:

    def test_set_and_get_attribute(self):
        test_predicate = rdflib.RDF.type
        test_value_1 = rdflib.term.Literal('test_value_1')
        test_value_2 = rdflib.term.Literal('test_value_2')

        wrapper = RdfWrapper(uri='test')
        wrapper.set_attribute(test_predicate, test_value_1)
        assert wrapper.get_attribute(test_predicate) == test_value_1

        # Setting the attribute another time should overwrite, and throw a
        # warning.
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            wrapper.set_attribute(test_predicate, test_value_2)
            assert len(w) == 1
            assert issubclass(w[-1].category, UserWarning)

        assert wrapper.get_attribute(test_predicate) == test_value_2

    def test_publish_as_nanopub_invalid_kwargs(self):
        wrapper = RdfWrapper(uri='test')
        with pytest.raises(ValueError):
            wrapper._publish_as_nanopub(introduces_concept='test', use_test_server=use_test_server)
        with pytest.raises(ValueError):
            wrapper._publish_as_nanopub(assertion_rdf='test', use_test_server=use_test_server)

    def test_publish_as_nanopub_double_derived_from(self):
        wrapper = RdfWrapper(uri='test', derived_from=['http://example.nl/workflow1'])
        with pytest.raises(ValueError):
            wrapper._publish_as_nanopub(derived_from=['http://example.nl/workflow2'], use_test_server=use_test_server)

    # @mock.patch('fairworkflows.rdf_wrapper.NanopubClient.publish')
    def test_publish_as_nanopub_with_kwargs(self):
        wrapper = RdfWrapper(uri='test', derived_from=['http://example.nl/workflow1'])
        wrapper.rdf.add((rdflib.URIRef('http://test'), rdflib.URIRef('http://test'), rdflib.Literal('test')))
        # attribute_asseriton_to_profile is kwarg for nanopub.Publication.from_assertion()
        wrapper._publish_as_nanopub(attribute_assertion_to_profile=True, use_test_server=use_test_server)
