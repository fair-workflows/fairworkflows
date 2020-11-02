from unittest.mock import patch

import pytest
import rdflib
from nanopub import Nanopub

from conftest import skip_if_nanopub_server_unavailable, read_rdf_test_resource
from fairworkflows import FairStep, namespaces


class TestFairStep:

    def test_inputs_outputs(self):
        test_inputs = ['test.org#input1', 'test.org#input2']
        test_outputs = ['test.org#output1', 'test.org#output2']
        step = FairStep()
        step.inputs = test_inputs
        step.outputs = test_outputs
        assert len(step.inputs) == 2
        assert len(step.outputs) == 2
        for input in step.inputs:
            assert str(input) in test_inputs
        for output in step.outputs:
            assert str(output) in test_outputs

        # test overwriting
        new_input = 'test.org#input3'
        new_output = 'test.org#output3'
        step.inputs = [new_input]
        step.outputs = [new_output]
        assert len(step.inputs) == 1
        assert len(step.outputs) == 1
        for input in step.inputs:
            assert str(input) == new_input
        for output in step.outputs:
            assert str(output) == new_output

    def test_construction_from_rdf(self):
        rdf = read_rdf_test_resource('sample_fairstep_nanopub.trig')
        uri = 'http://purl.org/np/RACLlhNijmCk4AX_2PuoBPHKfY1T6jieGaUPVFv-fWCAg#step'
        step = FairStep.from_rdf(rdf, uri)
        step.validate()

    def test_construction_from_rdf_filter_irrelevant_rdf_statements(self):
        """
        Test that only relevant RDF statements end up in the FairStep rdf when constructing from
        RDF.
        """
        rdf = read_rdf_test_resource('sample_fairstep_nanopub.trig')
        test_triple = (namespaces.NPX.test, namespaces.NPX.test, namespaces.NPX.test)
        rdf.add(test_triple)
        uri = 'http://purl.org/np/RACLlhNijmCk4AX_2PuoBPHKfY1T6jieGaUPVFv-fWCAg#step'
        step = FairStep.from_rdf(rdf, uri)
        step.validate()
        assert test_triple not in step.rdf

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_construction_from_nanopub(self):
        """
            Check that we can load a FairStep from known nanopub URIs for manual steps,
            that validation works, etc
        """

        nanopub_uris = [
            'http://purl.org/np/RA1pK9JQDyBHYGcl1zu4wh3BUmh47oE5RfldZh1Ml4XQw#step',
            'http://purl.org/np/RAz-A7EGUT9VCrSjK92HHc9DjwBssuc5eMdF09u1Psx5Q#step',
            'http://purl.org/np/RAfAJos5jSLTQ4sBoJj2Orau3xxa3AMa2QSvoEVLVtUwE#step'
        ]

        for uri in nanopub_uris:
            step = FairStep.from_nanopub(uri=uri)
            assert step is not None
            step.validate()
            assert step.is_manual_task
            assert not step.is_script_task

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_construction_from_nanopub_without_fragment(self):
        """
            Check that we can load a FairStep from known nanopub URIs also
            in cases where the full step URI is not used (i.e. missing a fragment).
            In other words, only the nanopub URI is given, but not the URI of the
            step itself within that nanopub.
        """

        nanopub_uris = [
            'http://purl.org/np/RA1pK9JQDyBHYGcl1zu4wh3BUmh47oE5RfldZh1Ml4XQw',
            'http://purl.org/np/RAz-A7EGUT9VCrSjK92HHc9DjwBssuc5eMdF09u1Psx5Q',
            'http://purl.org/np/RAfAJos5jSLTQ4sBoJj2Orau3xxa3AMa2QSvoEVLVtUwE'
        ]

        for uri in nanopub_uris:
            step = FairStep.from_nanopub(uri=uri)
            assert step is not None
            step.validate()
            assert step.is_manual_task
            assert not step.is_script_task

    def test_construction_from_function(self):
        def add(a: int, b: int):
            """
            Computational step adding two ints together.
            """
            return a + b

        step = FairStep.from_function(function=add)

        assert step is not None
        step.validate()
        assert not step.is_manual_task
        assert step.is_script_task

        assert step.__str__() is not None
        assert len(step.__str__()) > 0
        assert step.rdf is not None

    def test_validation(self):
        step = FairStep(uri='http://www.example.org/step')
        with pytest.raises(AssertionError):
            step.validate()

    @patch('fairworkflows.rdf_wrapper.NanopubClient.publish')
    @patch('fairworkflows.rdf_wrapper.NanopubClient.fetch')
    def test_modification_and_republishing(self, nanopub_fetch_mock,
                                           nanopub_publish_mock):

        test_uri = 'http://purl.org/np/RACLlhNijmCk4AX_2PuoBPHKfY1T6jieGaUPVFv-fWCAg#step'

        # Mock the Nanopub.fetch() method to return a locally sourced nanopub
        nanopub_rdf = read_rdf_test_resource('sample_fairstep_nanopub.trig')
        returned_nanopubobj = Nanopub(rdf=nanopub_rdf, source_uri=test_uri)
        nanopub_fetch_mock.return_value = returned_nanopubobj

        # 'Fetch' the nanopub as a fairstep, and attempt to publish it without modification
        preheat_oven = FairStep.from_nanopub(uri=test_uri)
        assert preheat_oven is not None
        assert not preheat_oven.is_modified
        original_uri = preheat_oven.uri
        with pytest.warns(Warning):
            preheat_oven.publish_as_nanopub()
        assert preheat_oven.uri == original_uri

        # Now modify the step description
        preheat_oven.description =  'Preheat an oven to 200 degrees C.'
        assert preheat_oven.is_modified is True
        preheat_oven.publish_as_nanopub()
        assert nanopub_publish_mock.called
        assert preheat_oven.uri != original_uri
        assert preheat_oven.is_modified is False

    def test_anonymise_rdf(self):
        """
        Test that the anonymize_rdf() function is correctly replacing nodes
        that contain the concept URI with the self_ref blank node.
        """

        test_uri = rdflib.URIRef('http://purl.org/sometest#step')

        # Set up some basic rdf graph to intialise a FairStep with
        rdf = rdflib.ConjunctiveGraph()
        rdf.add( (test_uri, rdflib.DCTERMS.description, rdflib.term.Literal('Some step description')) )
        step = FairStep.from_rdf(rdf=rdf, uri=test_uri)

        # Check that the FairStep initialisation has anonymised this rdf
        for s, p, o in step.rdf:
            assert s is not test_uri
            assert isinstance(s, rdflib.term.BNode)
            assert s is step.self_ref

    def test_shacl_does_not_validate(self):
        """
        Test a case where the plex shacl should not validate.
        """

        plex_rdf_trig = '''
        @prefix this: <http://www.example.org/step1> .
        @prefix sub: <http://www.example.org/step1#> .
        @prefix pplan: <http://purl.org/net/p-plan#> .
        @prefix pwo: <http://purl.org/spar/pwo/> .

        {
            this: a pplan:Step .

            sub:step1 pplan:isStepOfPlan this:;
                a pplan:Step .
        }
        '''

        g = rdflib.Graph()
        g.parse(data=plex_rdf_trig, format='trig')

        step = FairStep.from_rdf(rdf=g,  uri='http://www.example.org/step1',
                                 remove_irrelevant_triples=False)

        with pytest.raises(AssertionError):
            step.shacl_validate()
