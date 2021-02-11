import sys
from typing import Tuple
from unittest.mock import patch

import pytest
import rdflib
from rdflib import DCTERMS, OWL, RDF
from nanopub import Publication

from conftest import skip_if_nanopub_server_unavailable, read_rdf_test_resource
from fairworkflows import FairStep, namespaces, FairVariable, is_fairworkflow
from fairworkflows.fairstep import _extract_outputs_from_function, is_fairstep
from fairworkflows.rdf_wrapper import replace_in_rdf
from fairworkflows import LinguisticSystem

def test_construct_fair_variable_get_name_from_uri():
    variable = FairVariable(name=None, uri='http:example.org#input1', computational_type='int')
    assert variable.name == 'input1'
    assert variable.computational_type == 'int'


class TestFairStep:
    def test_inputs(self):
        test_inputs = [FairVariable('input1', 'int'), FairVariable('input2', 'str')]
        step = FairStep()
        step.inputs = test_inputs
        assert len(step.inputs) == 2
        assert (rdflib.term.BNode('input1'), rdflib.RDF.type, namespaces.PPLAN.Variable) in step.rdf
        for input in step.inputs:
            assert str(input.name) in [test_input.name for test_input in test_inputs]
            assert str(input.computational_type) in [test_input.computational_type for test_input in test_inputs]

        # test overwriting
        new_input = FairVariable('input3', 'int')
        step.inputs = [new_input]
        assert len(step.inputs) == 1

    def test_outputs(self):
        test_outputs = [FairVariable('output1', 'int'), FairVariable('output2', 'str')]
        step = FairStep()
        step.outputs = test_outputs
        assert len(step.outputs) == 2
        assert (rdflib.term.BNode('output1'),
                rdflib.RDF.type, namespaces.PPLAN.Variable) in step.rdf
        for output in step.outputs:
            assert str(output.name) in [test_output.name for test_output in test_outputs]
            assert str(output.computational_type) in [test_output.computational_type for test_output in test_outputs]

        # test overwriting
        outputs = FairVariable('output3', 'int')
        step.outputs = [outputs]
        assert len(step.outputs) == 1

    def test_setters(self):
        step = FairStep()
        step.is_pplan_step = True
        assert step.is_pplan_step
        step.is_manual_task = True
        assert step.is_manual_task
        step.is_script_task = True
        assert step.is_script_task
        assert not step.is_manual_task  # script and manual task are mutually exclusive
        step.is_script_task = False
        step.is_script_task = False  # Test setting to current value
        assert not step.is_script_task

    def test_construction_from_rdf(self):
        rdf = read_rdf_test_resource('sample_fairstep_nanopub.trig')
        uri = 'http://purl.org/np/RACLlhNijmCk4AX_2PuoBPHKfY1T6jieGaUPVFv-fWCAg#step'
        step = FairStep.from_rdf(rdf, uri)
        step.validate()

    def test_construction_from_rdf_remove_irrelevant_triples(self):
        """
        Test that only relevant RDF statements end up in the FairStep rdf when constructing from
        RDF.
        """
        rdf = read_rdf_test_resource('sample_fairstep_nanopub.trig')
        uri = 'http://purl.org/np/RACLlhNijmCk4AX_2PuoBPHKfY1T6jieGaUPVFv-fWCAg#step'
        this = rdflib.URIRef(uri)
        test_namespace = rdflib.Namespace(
            'http://purl.org/np/RACLlhNijmCk4AX_2PuoBPHKfY1T6jieGaUPVFv-fWCAg#')
        test_irrelevant_triples = [
            # A random test statement that has nothing to do with this step
            (test_namespace.test, test_namespace.test, test_namespace.test),
            # A precedes relation with another step that is part of the workflow RDF, not this
            # step RDF.
            (this, namespaces.DUL.precedes, test_namespace.other_step),
            # The workflow that it is part of
            (this, namespaces.PPLAN.isStepOfPlan, test_namespace.workflow1),
            # A different step that is also a manual task
            (test_namespace.other_step, rdflib.RDF.type, namespaces.BPMN.ManualTask)

        ]
        test_relevant_triples = [
            # An input variable of the step
            (this, namespaces.PPLAN.hasInputVar, test_namespace.input1),
            # A triple saying something about the input of the step, therefore relevant!
            (test_namespace.input1, rdflib.RDF.type, namespaces.PPLAN.Variable)
        ]
        for triple in test_relevant_triples + test_irrelevant_triples:
            rdf.add(triple)
        step = FairStep.from_rdf(rdf, uri, remove_irrelevant_triples=True)
        step.validate()

        # Replace blank nodes with the original URI so we can test the results
        replace_in_rdf(step.rdf, oldvalue=step.self_ref, newvalue=rdflib.URIRef(uri))
        for relevant_triple in test_relevant_triples:
            assert relevant_triple in step.rdf
        for irrelevant_triple in test_irrelevant_triples:
            assert irrelevant_triple not in step.rdf

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

    def test_construction_from_non_marked_function(self):
        def add(a: int, b: int) -> int:
            """
            Computational step adding two ints together.
            """
            return a + b
        with pytest.raises(ValueError):
            FairStep.from_function(add)

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
        returned_nanopubobj = Publication(rdf=nanopub_rdf, source_uri=test_uri)
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

        n_triples_before = len(step.rdf)
        with pytest.raises(AssertionError):
            step.shacl_validate()

        assert len(step.rdf) == n_triples_before, 'shacl_validate mutated RDF'


def test_is_fairstep_decorator():
    @is_fairstep(label='test_label')
    def add(a: int, b: int) -> int:
        """
        Computational step adding two ints together.
        """
        return a + b

    assert hasattr(add(1,2), '_fairstep')

def test_decorator_semantic_types():
    test_types_a = ['http://www.example.org/distance', 'http://www.example.org/number']
    test_type_output = 'http://www.example.org/walrus'
    @is_fairstep(label='A test step', a=test_types_a, returns=test_type_output)
    def test_step(a:float, b:float) -> float:
        return a + b

    assert hasattr(test_step, '_fairstep')
    for var in test_step._fairstep.inputs:
        assert namespaces.PPLAN.Variable not in var.semantic_types
        if var.name == 'a':
            assert var.computational_type == 'float'
            for sem_type in test_types_a:
                assert rdflib.URIRef(sem_type) in var.semantic_types
            break
    else:
        raise

    assert test_step._fairstep.language is not None
    assert isinstance(test_step._fairstep.language, LinguisticSystem)
    assert (None, RDF.type, namespaces.SCHEMAORG.ComputerLanguage) in test_step._fairstep._rdf
    assert (None, DCTERMS.language, None) in test_step._fairstep._rdf
    assert (None, OWL.versionInfo, None) in test_step._fairstep._rdf
    assert 'python' in test_step._fairstep.language.label


def test_decorator_semantic_types_multiple_outputs():
    output_tuple = ('http://www.example.org/walrus', 'http://www.example.org/krill')

    @is_fairstep(label='A test step', returns=output_tuple)
    def test_step(a:float, b:float) -> Tuple[float, float]:
        return a + b, a - b

    assert hasattr(test_step, '_fairstep')
    for i, var in enumerate(test_step._fairstep.outputs):
        assert namespaces.PPLAN.Variable not in var.semantic_types
        assert var.computational_type == 'float'
        assert rdflib.URIRef(output_tuple[i]) in var.semantic_types

def test_extract_outputs_from_function_multiple_outputs():
    # Note this function returns a tuple, and thus has multiple outputs
    def divmod(a: int, b: int) -> Tuple[int, int]:
        """
        Computational step dividing a with b, additionaly returning the modulo.
        """
        return a // b, a % b

    result = _extract_outputs_from_function(divmod, {})
    assert set(result) == {FairVariable('out1', 'int'),
                           FairVariable('out2', 'int')}
