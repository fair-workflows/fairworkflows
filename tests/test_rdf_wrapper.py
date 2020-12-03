import warnings
from unittest import mock

import pytest
import rdflib

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

    def test_publish_as_nanopub_introduces_concept_kwarg(self):
        wrapper = RdfWrapper(uri='test')
        with pytest.raises(ValueError):
            wrapper._publish_as_nanopub(introduces_concept='test')

    @mock.patch('fairworkflows.rdf_wrapper.NanopubClient.publish')
    def test_publish_as_nanopub_with_kwargs(self, nanopub_wrapper_publish_mock):
        wrapper = RdfWrapper(uri='test')
        wrapper.rdf.add((rdflib.Literal('test'), rdflib.Literal('test'), rdflib.Literal('test')))
        # attribute_assertion_to_profile is a kwarg for nanopub.Publication.from_assertion()
        wrapper._publish_as_nanopub(attribute_assertion_to_profile=True)

    def test_merge_derived_from(self):
        wrapper = RdfWrapper(uri='test')
        result = wrapper._merge_derived_from(user_derived_from='test1', our_derived_from='test2')
        assert result == ['test1', 'test2']
        result = wrapper._merge_derived_from(user_derived_from=['test1', 'test2'],
                                             our_derived_from='test3')
        assert result == ['test1', 'test2', 'test3']
