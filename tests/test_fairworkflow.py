import inspect
import warnings
from unittest import mock

import pytest
import rdflib
from requests import HTTPError

from conftest import skip_if_nanopub_server_unavailable, read_rdf_test_resource
from fairworkflows import FairWorkflow, FairStep, namespaces, FairVariable, is_fairstep, is_fairworkflow
from fairworkflows.rdf_wrapper import replace_in_rdf
from nanopub import Publication


class TestFairWorkflow:
    test_description = 'This is a test workflow.'
    test_label = 'Test'
    test_step_uris = [
        'http://www.example.org/step1',
        'http://www.example.org/step2',
        'http://www.example.org/step3'
    ]

    @pytest.fixture()
    def test_step1(self):
        step = FairStep(uri=self.test_step_uris[0])
        step.description = 'Step 1'
        return step

    @pytest.fixture()
    def test_step2(self):
        step = FairStep(uri=self.test_step_uris[1])
        step.description = 'Step 2'
        return step

    @pytest.fixture()
    def test_step3(self):
        step = FairStep(uri=self.test_step_uris[2])
        step.description = 'Step 3'
        return step

    @pytest.fixture()
    def test_workflow(self, test_step1, test_step2, test_step3):
        workflow = FairWorkflow(description=self.test_description, label=self.test_label,
                                first_step=test_step1)
        workflow.add(test_step2, follows=test_step1)
        workflow.add(test_step3, follows=test_step2)
        return workflow

    def test_build(self, test_step1, test_step2, test_step3):
        workflow = FairWorkflow(description=self.test_description, label=self.test_label)

        assert workflow is not None
        assert str(workflow.description) == self.test_description

        with pytest.raises(AssertionError):
            workflow.validate()

        workflow.add(test_step2, follows=test_step1)
        workflow.add(test_step3, follows=test_step2)

        with pytest.raises(AssertionError):
            workflow.validate()

        workflow.first_step = test_step1

        workflow.validate()

        assert workflow.__str__() is not None
        assert len(workflow.__str__()) > 0
        assert workflow.rdf is not None

    def test_build_including_step_without_uri(self):
        step1 = FairStep()
        workflow = FairWorkflow()
        workflow.add(step1)
        assert (rdflib.URIRef('None'), None, None) not in workflow.rdf
        assert (None, None, rdflib.URIRef('None')) not in workflow.rdf

    def test_construct_from_rdf_uri_not_in_subjects(self):
        rdf = read_rdf_test_resource('test_workflow.trig')
        # This URI is not in the subject of this RDF:
        uri = 'http://www.example.org/some-random-uri'
        with pytest.raises(ValueError):
            FairWorkflow.from_rdf(rdf, uri, force=False)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            FairWorkflow.from_rdf(rdf, uri, force=True)
            assert len(w) == 1

    @mock.patch('fairworkflows.fairworkflow.FairWorkflow._fetch_step')
    def test_construct_from_rdf_fetch_steps(self, mock_fetch_step, test_step1):
        """
        Construct FairWorkflow from RDF that only includes URIs that point to
        steps which we should fetch.
        """
        mock_fetch_step.return_value = test_step1
        rdf = read_rdf_test_resource('test_workflow.trig')
        uri = 'http://www.example.org/workflow1'
        workflow = FairWorkflow.from_rdf(rdf, uri, fetch_references=True)
        assert len(workflow._steps) == 1
        assert mock_fetch_step.call_count == 1
        assert list(workflow._steps.values())[0] == test_step1

    def test_construct_from_rdf_do_not_fetch_steps(self):
        """
        Construct FairWorkflow from RDF that only includes URIs that point to
        steps. We choose not to fetch these steps and have empty fair steps
        pointing to the uri.
        """
        rdf = read_rdf_test_resource('test_workflow.trig')
        uri = 'http://www.example.org/workflow1'
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            workflow = FairWorkflow.from_rdf(rdf, uri, fetch_references=False)
            assert len(w) == 1, 'Exactly 1 warning should be raised'
            assert 'Could not get detailed information' in str(w[0].message)
        assert len(workflow._steps) == 1

    @mock.patch('fairworkflows.fairworkflow.FairWorkflow._fetch_step')
    def test_construct_from_rdf_fetch_steps_fails(self, mock_fetch_step):
        """
        Construct FairWorkflow from RDF that only includes URIs that point to
        steps. Fetching the step fails in this scenario.
        """
        mock_fetch_step.return_value = None
        rdf = read_rdf_test_resource('test_workflow.trig')
        uri = 'http://www.example.org/workflow1'
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            workflow = FairWorkflow.from_rdf(rdf, uri, fetch_references=True)
            assert len(w) == 1, 'Exactly 1 warning should be raised'
            assert 'Could not get detailed information' in str(w[0].message)
        assert len(workflow._steps) == 1

    def test_construct_from_rdf_remove_irrelevant_triples(self):
        rdf = read_rdf_test_resource('test_workflow.trig')
        uri = 'http://www.example.org/workflow1'
        sub = rdflib.Namespace('http://www.example.org/workflow1#')
        step1 = rdflib.URIRef('http://www.example.org/step1')
        test_irrelevant_triples = [
            # A random test statement that has nothing to do with this step
            (sub.test, sub.test, sub.test)
        ]
        test_relevant_triples = [
            # Dul precedes statements are relevant
            (step1, namespaces.DUL.precedes, sub.step2),
            # Properties of the workflow are relevant
            (rdflib.URIRef(uri), sub.hasSecurityLevel, sub.highSecurity),
            # And the properties of those properties
            (sub.highSecurity, sub.color, rdflib.Literal('Red')),
        ]
        for triple in test_relevant_triples + test_irrelevant_triples:
            rdf.set(triple)  # Some triples are already in there, so we use set to not duplicate
        workflow = FairWorkflow.from_rdf(rdf, uri, fetch_references=False,
                                         remove_irrelevant_triples=True)
        workflow.validate()
        # Replace blank nodes with the original URI so we can test the results
        replace_in_rdf(workflow.rdf, oldvalue=workflow.self_ref, newvalue=rdflib.URIRef(uri))

        for relevant_triple in test_relevant_triples:
            assert relevant_triple in workflow.rdf
        for irrelevant_triple in test_irrelevant_triples:
            assert irrelevant_triple not in workflow.rdf

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_construction_from_nanopub(self):
        """Test loading a FairWorkflow from known nanopub URI."""

        # Test for a url both with fragment specified and without
        uris = [
            'http://purl.org/np/RAxae-D21NYtRL7Sd5xU6gZEkUUQ6mj4VUUwgD8BLgMzc#plan',
            'http://purl.org/np/RAxae-D21NYtRL7Sd5xU6gZEkUUQ6mj4VUUwgD8BLgMzc'
        ]
        for uri in uris:
            workflow = FairWorkflow.from_nanopub(uri=uri)
            assert workflow is not None
            workflow.validate()
            steps = list(workflow)
            assert len(steps) > 0

    @mock.patch('fairworkflows.fairworkflow.FairStep.from_nanopub')
    def test_fetch_step_404(self, mock_from_nanopub, test_workflow):
        response = mock.MagicMock(status_code=404)
        mock_from_nanopub.side_effect = HTTPError(response=response)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = test_workflow._fetch_step(uri='test_uri')
            assert len(w) == 1, 'Exactly 1 warning should be raised'
            assert 'Failed fetching' in str(w[0].message)
        assert result is None

    @mock.patch('fairworkflows.fairworkflow.FairStep.from_nanopub')
    def test_fetch_step_500(self, mock_from_nanopub, test_workflow):
        response = mock.MagicMock(status_code=500)
        mock_from_nanopub.side_effect = HTTPError(response=response)
        with pytest.raises(HTTPError):
            test_workflow._fetch_step(uri='test_uri')

    def test_iterator(self, test_step1, test_step2, test_step3, test_workflow):
        """Test iterating over the workflow."""
        right_order_steps = [test_step1, test_step2, test_step3]
        workflow_steps = list(test_workflow)
        assert len(workflow_steps) == len(right_order_steps)
        for i, step in enumerate(workflow_steps):
            assert step == right_order_steps[i]

    def test_iterator_one_step(self, test_step1):
        workflow = FairWorkflow()
        workflow.add(test_step1)
        workflow_steps = list(workflow)
        assert len(workflow_steps) == 1

    def test_iterator_sorting_failed(self, test_step1, test_step2):
        workflow = FairWorkflow()
        workflow.add(test_step1)

        # Add a step that follows a step not in the workflow. There are now 2
        # steps in the workflow that are not connected by a precedes
        # predicate. This should lead to a RuntimeError.
        workflow.add(test_step2, follows=FairStep('not in workflow'))
        with pytest.raises(RuntimeError):
            list(workflow)

    @mock.patch.dict('sys.modules', {'graphviz': None})
    def test_draw_without_graphviz_module(self, tmp_path, test_workflow):
        """Test draw method without graphviz python module installed."""
        with pytest.raises(ImportError):
            test_workflow.draw(filepath=tmp_path)

    def test_draw_with_graphviz_module_without_dependency(self, tmp_path, test_workflow):
        """
        Test draw method with graphviz python module installed,
        but not graphviz software
        """
        mock_graphviz = mock.MagicMock()
        mock_graphviz.ExecutableNotFound = Exception
        mock_graphviz.render.side_effect = mock_graphviz.ExecutableNotFound()

        with mock.patch.dict('sys.modules', {'graphviz': mock_graphviz}):
            with pytest.raises(RuntimeError):
                test_workflow.draw(filepath=str(tmp_path))

    def test_draw_with_graphviz_module_and_dependency(self, tmp_path, test_workflow):
        """
        Test draw method with graphviz python module and graphviz software
        installed
        """
        test_workflow.draw(filepath=str(tmp_path))

    @mock.patch.dict('sys.modules', {'graphviz': None})
    def test_display_without_graphviz_module(self, test_workflow):
        """Test display method without graphviz python module installed."""
        with pytest.raises(ImportError):
            test_workflow.display(full_rdf=True)

    def test_display_with_graphviz_module_and_dependency(self, test_workflow):
        """
        Test display method with graphviz python module and graphviz software
        installed
        """
        test_workflow.display(full_rdf=True)

    @mock.patch('fairworkflows.rdf_wrapper.NanopubClient.publish')
    def test_publish_as_nanopub(self, mock_publish, test_workflow):
        test_published_uris = ['www.example.org/published_step1#step',
                               'www.example.org/published_step2#step',
                               'www.example.org/published_step3#step',
                               'www.example.org/published_workflow#workflow']
        mock_publish.side_effect = [
            {'concept_uri': test_published_uris[0]},  # first call
            {'concept_uri': test_published_uris[1]},
            {'concept_uri': test_published_uris[2]},
            {'concept_uri': test_published_uris[3]}   # Last call
        ]
        with pytest.raises(RuntimeError):
            # 'Publishing a workflow with unpublished steps must raise RunTimeError'
            test_workflow.publish_as_nanopub()
        # First publish the steps
        for step in test_workflow:
            step.publish_as_nanopub()
        pubinfo = test_workflow.publish_as_nanopub()
        assert pubinfo['concept_uri'] == 'www.example.org/published_workflow#workflow'
        assert mock_publish.call_count == 4  # 1 workflow, 3 steps
        for step in test_workflow:
            assert step.uri in test_published_uris
            assert ((rdflib.URIRef(step.uri), None, None) in test_workflow.rdf
                    or (None, None, rdflib.URIRef(step.uri)) in test_workflow.rdf), \
                'The new step URIs are not in the workflow'
        for uri in self.test_step_uris:
            assert ((rdflib.URIRef(uri), None, None) not in test_workflow.rdf
                    and (None, None, rdflib.URIRef(uri)) not in test_workflow.rdf), \
                'The old step URIs are still in the workflow'

    @mock.patch('fairworkflows.rdf_wrapper.NanopubClient.publish')
    def test_publish_as_nanopub_no_modifications(self, mock_publish, test_workflow):
        """
        Test case of an already published workflow that itself nor its steps are not modified.
        """
        for step in test_workflow:
            step._is_modified = False
            step._is_published = True
        test_workflow._is_modified = False
        test_workflow._is_published = True
        pubinfo = test_workflow.publish_as_nanopub()
        assert mock_publish.call_count == 0
        assert pubinfo['nanopub_uri'] is None

    def test_workflow_construction_and_execution(self):
        """
        Construct a workflow using the is_fairstep and is_fairworkflow decorators
        and check that execution and returned provenance is as expected.
        """
        @is_fairstep(label='Addition')
        def add(a:float, b:float) -> float:
            """Adding up numbers."""
            return a + b

        @is_fairstep(label='Subtraction')
        def sub(a: float, b: float) -> float:
            """Subtracting numbers."""
            return a - b

        @is_fairstep(label='Multiplication')
        def mul(a: float, b: float) -> float:
            """Multiplying numbers."""
            return a * b

        @is_fairstep(label='A strange step with little use')
        def weird(a: float, b:float) -> float:
            """A weird function"""
            return a * 2 + b * 4

        @is_fairworkflow(label='My Workflow')
        def my_workflow(in1, in2, in3):
            """
            A simple addition, subtraction, multiplication workflow
            """
            t1 = add(in1, in2)  # 5
            t2 = sub(in1, in2)  # -3
            t3 = weird(t1, in3)  # 10 + 12 = 22
            t4 = mul(t3, t2)  # 22 * -3 = 66
            return t4

        fw = FairWorkflow.from_function(my_workflow)

        assert isinstance(fw, FairWorkflow)

        result, prov = fw.execute(1, 4, 3)
        assert result == -66
        assert isinstance(prov, Publication)

    def test_workflow_complex_serialization(self):
        class OtherType:
            def __init__(self, message):
                self.message = message

        @is_fairstep(label='Returns the thing it recieves...')
        def return_that_object(im:OtherType) -> OtherType:
            return im

        @is_fairworkflow(label='A workflow that passes an object reference around.')
        def process_image(im: OtherType):
            return return_that_object(im)

        obj = OtherType('I could be e.g. a PIL Image')
        fw = FairWorkflow.from_function(process_image)
        result, prov = fw.execute(obj)
        assert isinstance(result, type(obj))
        assert result.message == obj.message
        assert isinstance(prov, Publication)
        
    def test_workflow_non_decorated_step(self):
        def return_value(a: float) -> float:
            """Return the input value. NB: no is_fairstep decorator!"""
            return a

        with pytest.raises(TypeError) as e:
            @is_fairworkflow(label='My Workflow')
            def my_workflow(in1):
                """
                A simple workflow
                """
                return return_value(in1)
        assert "The workflow does not return a 'promise'" in str(e.value)

    def test_workflow_mixed_decorated_steps(self):
        def add(a: float, b: float) -> float:
            """Adding up numbers. NB: no is_fairstep decorator!"""
            return a + b

        @is_fairstep(label='Subtraction')
        def sub(a: float, b: float) -> float:
            """Subtracting numbers."""
            return a - b

        with pytest.raises(TypeError) as e:
            @is_fairworkflow(label='My Workflow')
            def my_workflow(in1, in2):
                """
                A simple addition, subtraction workflow
                """
                return add(in1, sub(in2, in2))
        assert ("Marking the function as workflow with `is_fairworkflow` decorator failed. "
                in str(e.value))
        assert "unsupported operand type(s)" in str(e.value)

    def test_get_arguments_dict(self):
        args = (1, 2)
        kwargs = {'c': 3, 'd': 4}

        def func(a, b, c, d):
            return

        result = FairWorkflow._get_arguments_dict(args, kwargs, inspect.signature(func))
        assert result == {'a': 1, 'b': 2, 'c': 3, 'd': 4}
