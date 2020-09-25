import pytest
import requests
from unittest.mock import patch
import rdflib

from fairworkflows import FairStep, Nanopub
from fairworkflows.config import TESTS_RESOURCES

BAD_GATEWAY = 502
NANOPUB_SERVER = 'http://purl.org/np/'
SERVER_UNAVAILABLE = 'Nanopub server is unavailable'


def nanopub_server_unavailable():
    response = requests.get(NANOPUB_SERVER)

    return response.status_code == BAD_GATEWAY


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

    @pytest.mark.flaky(max_runs=10)
    @pytest.mark.skipif(nanopub_server_unavailable(), reason=SERVER_UNAVAILABLE)
    def test_construction_from_nanopub(self):
        """
            Check that we can load a FairStep from known nanopub URIs for manual steps,
            that validation works, etc
        """

        nanopub_uris = [
            'http://purl.org/np/RACLlhNijmCk4AX_2PuoBPHKfY1T6jieGaUPVFv-fWCAg#step',
            'http://purl.org/np/RANBLu3UN2ngnjY5Hzrn7S5GpqFdz8_BBy92bDlt991X4#step',
            'http://purl.org/np/RA5D8NzM2OXPZAWNlADQ8hZdVu1k0HnmVmgl20apjhU8M#step'
        ]

        for uri in nanopub_uris:
            step = FairStep.from_nanopub(uri=uri)
            assert step is not None
            step.validate()
            assert step.is_manual_task
            assert not step.is_script_task

    @pytest.mark.flaky(max_runs=10)
    @pytest.mark.skipif(nanopub_server_unavailable(), reason=SERVER_UNAVAILABLE)
    def test_construction_from_nanopub_without_fragment(self):
        """
            Check that we can load a FairStep from known nanopub URIs also
            in cases where the full step URI is not used (i.e. missing a fragment).
            In other words, only the nanopub URI is given, but not the URI of the
            step itself within that nanopub.
        """

        nanopub_uris = [
            'http://purl.org/np/RACLlhNijmCk4AX_2PuoBPHKfY1T6jieGaUPVFv-fWCAg',
            'http://purl.org/np/RANBLu3UN2ngnjY5Hzrn7S5GpqFdz8_BBy92bDlt991X4',
            'http://purl.org/np/RA5D8NzM2OXPZAWNlADQ8hZdVu1k0HnmVmgl20apjhU8M'
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

    @patch('fairworkflows.nanopub_wrapper.publish')
    @patch('fairworkflows.nanopub.Nanopub.fetch')
    def test_modification_and_republishing(self, nanopub_fetch_mock,
                                           nanopub_wrapper_publish_mock):

        test_uri = 'http://purl.org/np/RACLlhNijmCk4AX_2PuoBPHKfY1T6jieGaUPVFv-fWCAg#step'

        # Mock the Nanopub.fetch() method to return a locally sourced nanopub
        nanopub_rdf = rdflib.ConjunctiveGraph()
        nanopub_rdf.parse(str(TESTS_RESOURCES / 'sample_fairstep_nanopub.trig'),
                          format='trig')
        returned_nanopubobj = Nanopub.NanopubObj(rdf=nanopub_rdf, source_uri=test_uri)
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
        assert nanopub_wrapper_publish_mock.called
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
