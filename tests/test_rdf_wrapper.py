import warnings

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
