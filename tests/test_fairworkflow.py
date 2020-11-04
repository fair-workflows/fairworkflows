import warnings
from unittest import mock

import pytest
import rdflib
from rdflib.compare import isomorphic
from requests import HTTPError

from conftest import skip_if_nanopub_server_unavailable, read_rdf_test_resource
from fairworkflows import FairWorkflow, FairStep, add_step, namespaces
from fairworkflows.rdf_wrapper import replace_in_rdf


class TestFairWorkflow:
    test_description = 'This is a test workflow.'
    test_label = 'Test'
    workflow = FairWorkflow(description=test_description, label=test_label)
    test_step_uris = [
        'http://www.example.org/step1',
        'http://www.example.org/step2',
        'http://www.example.org/step3'
    ]
    step1 = FairStep(uri=test_step_uris[0])
    step2 = FairStep(uri=test_step_uris[1])
    step3 = FairStep(uri=test_step_uris[2])

    workflow.first_step = step1
    workflow.add(step2, follows=step1)
    workflow.add(step3, follows=step2)

    for step in workflow:
        step.is_pplan_step = True

    def test_build(self):
        workflow = FairWorkflow(description=self.test_description, label=self.test_label)

        assert workflow is not None
        assert str(workflow.description) == self.test_description

        with pytest.raises(AssertionError):
            workflow.validate()

        workflow.add(self.step2, follows=self.step1)
        workflow.add(self.step3, follows=self.step2)

        with pytest.raises(AssertionError):
            workflow.validate()

        workflow.first_step = self.step1

        workflow.validate()

        assert workflow.__str__() is not None
        assert len(workflow.__str__()) > 0
        assert workflow.rdf is not None

    def test_construct_from_rdf_uri_not_in_subjects(self):
        rdf = read_rdf_test_resource('test_workflow_including_steps.trig')
        # This URI is not in the subject of this RDF:
        uri = 'http://www.example.org/some-random-uri'
        with pytest.raises(ValueError):
            FairWorkflow.from_rdf(rdf, uri, force=False)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            FairWorkflow.from_rdf(rdf, uri, force=True)
            assert len(w) == 1

    def test_construct_from_rdf_including_steps(self):
        """
        Construct FairWorkflow from RDF that includes detailed information
        about steps.
        """
        rdf = read_rdf_test_resource('test_workflow_including_steps.trig')
        uri = 'http://www.example.org/workflow1'
        workflow = FairWorkflow.from_rdf(rdf, uri, fetch_references=False)
        new_rdf = read_rdf_test_resource('test_workflow_including_steps.trig')
        assert rdflib.compare.isomorphic(rdf, new_rdf),\
            'The user RDF was altered after constructing a Fairworkflow ' \
            'object from it'
        valid_step_uris = [uri + '#step1', uri + '#step2', uri + '#step3']
        steps = list(workflow)
        assert len(steps) == 3
        for step in steps:
            step.validate()
            assert step.uri in valid_step_uris

        workflow.validate()

        # Check that workflow rdf passes plex shacl validation
        workflow.shacl_validate()

    @mock.patch('fairworkflows.fairworkflow.FairWorkflow._fetch_step')
    def test_construct_from_rdf_fetch_steps(self, mock_fetch_step):
        """
        Construct FairWorkflow from RDF that only includes URIs that point to
        steps which we should fetch.
        """
        mock_fetch_step.return_value = self.step1
        rdf = read_rdf_test_resource('test_workflow_excluding_steps.trig')
        uri = 'http://www.example.org/workflow1'
        workflow = FairWorkflow.from_rdf(rdf, uri, fetch_references=True)
        assert len(workflow._steps) == 1
        assert mock_fetch_step.call_count == 1
        assert list(workflow._steps.values())[0] == self.step1

    def test_construct_from_rdf_do_not_fetch_steps(self):
        """
        Construct FairWorkflow from RDF that only includes URIs that point to
        steps. We choose not to fetch these steps and have empty fair steps
        pointing to the uri.
        """
        rdf = read_rdf_test_resource('test_workflow_excluding_steps.trig')
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
        rdf = read_rdf_test_resource('test_workflow_excluding_steps.trig')
        uri = 'http://www.example.org/workflow1'
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            workflow = FairWorkflow.from_rdf(rdf, uri, fetch_references=True)
            assert len(w) == 1, 'Exactly 1 warning should be raised'
            assert 'Could not get detailed information' in str(w[0].message)
        assert len(workflow._steps) == 1

    def test_construct_from_rdf_remove_irrelevant_triples(self):
        rdf = read_rdf_test_resource('test_workflow_including_steps.trig')
        uri = 'http://www.example.org/workflow1'
        sub = rdflib.Namespace('http://www.example.org/workflow1#')
        test_irrelevant_triples = [
            # A random test statement that has nothing to do with this step
            (sub.test, sub.test, sub.test),
            # A statement about a step, this will be in the RDF of the related FairStep objects
            (sub.step1, rdflib.RDFS.label, rdflib.Literal("Step 1"))
        ]
        test_relevant_triples = [
            # Dul precedes statements are relevant
            (sub.step1, namespaces.DUL.precedes, sub.step2),
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
    def test_fetch_step_404(self, mock_from_nanopub):
        response = mock.MagicMock(status_code=404)
        mock_from_nanopub.side_effect = HTTPError(response=response)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = self.workflow._fetch_step(uri='test_uri')
            assert len(w) == 1, 'Exactly 1 warning should be raised'
            assert 'Failed fetching' in str(w[0].message)
        assert result is None

    @mock.patch('fairworkflows.fairworkflow.FairStep.from_nanopub')
    def test_fetch_step_500(self, mock_from_nanopub):
        response = mock.MagicMock(status_code=500)
        mock_from_nanopub.side_effect = HTTPError(response=response)
        with pytest.raises(HTTPError):
            self.workflow._fetch_step(uri='test_uri')

    def test_iterator(self):
        """Test iterating over the workflow."""
        right_order_steps = [self.step1, self.step2, self.step3]
        workflow_steps = list(self.workflow)
        assert len(workflow_steps) == len(right_order_steps)
        for i, step in enumerate(workflow_steps):
            assert step == right_order_steps[i]

    def test_iterator_one_step(self):
        workflow = FairWorkflow()
        workflow.add(self.step1)
        workflow_steps = list(workflow)
        assert len(workflow_steps) == 1

    def test_iterator_sorting_failed(self):
        workflow = FairWorkflow()
        workflow.add(self.step1)

        # Add a step that follows a step not in the workflow. There are now 2
        # steps in the workflow that are not connected by a precedes
        # predicate. This should lead to a RuntimeError.
        workflow.add(self.step2, follows=FairStep('not in workflow'))
        with pytest.raises(RuntimeError):
            list(workflow)

    def test_validate_inputs_outputs(self):
        # Step 1 precedes step 2, so valid if input of 2 is output of 1
        self.step1.outputs = ['var1']
        self.step2.inputs = ['var1']
        self.workflow.validate()

        # Step 1 precedes step 2, so invalid if input of 1 is output of 2
        self.step1.inputs = ['var1']
        self.step2.outputs = ['var1']
        with pytest.raises(AssertionError):
            self.workflow.validate()

    def test_unbound_inputs(self):
        self.step1.inputs = ['var1']
        self.step1.outputs = ['var2']
        self.step2.inputs = ['var2', 'var3']
        self.step2.outputs = []
        unbound_input_uris = [str(input) for input, step in
                              self.workflow.unbound_inputs]
        assert sorted(unbound_input_uris) == sorted(['var1', 'var3'])

    def test_unbound_outputs(self):
        self.step1.inputs = []
        self.step1.outputs = ['var1', 'var2']
        self.step2.inputs = ['var2']
        self.step2.outputs = ['var3']
        unbound_output_uris = [str(output) for output, step in
                               self.workflow.unbound_outputs]
        assert sorted(unbound_output_uris) == sorted(['var1', 'var3'])

    @mock.patch('fairworkflows.rdf_wrapper.NanopubClient.publish')
    def test_publish(self, nanopub_wrapper_publish_mock):
        """
        Test (mock) publishing of workflow
        """
        self.workflow.publish_as_nanopub()

    def test_decorator(self):
        workflow = FairWorkflow(description='This is a test workflow.', label=self.test_label)

        @add_step(workflow)
        def test_fn(x, y):
            return x * y

        with pytest.raises(AssertionError):
            workflow.validate()

        test_fn(1, 2)

        workflow.validate()

    @mock.patch.dict('sys.modules', {'graphviz': None})
    def test_draw_without_graphviz_module(self, tmp_path):
        """Test draw method without graphviz python module installed."""
        with pytest.raises(ImportError):
            self.workflow.draw(filepath=tmp_path)

    def test_draw_with_graphviz_module_without_dependency(self, tmp_path):
        """
        Test draw method with graphviz python module installed,
        but not graphviz software
        """
        mock_graphviz = mock.MagicMock()
        mock_graphviz.ExecutableNotFound = Exception
        mock_graphviz.render.side_effect = mock_graphviz.ExecutableNotFound()

        with mock.patch.dict('sys.modules', {'graphviz': mock_graphviz}):
            with pytest.raises(RuntimeError):
                self.workflow.draw(filepath=str(tmp_path))

    def test_draw_with_graphviz_module_and_dependency(self, tmp_path):
        """
        Test draw method with graphviz python module and graphviz software
        installed
        """
        self.workflow.draw(filepath=str(tmp_path))

    @mock.patch.dict('sys.modules', {'graphviz': None})
    def test_display_without_graphviz_module(self):
        """Test display method without graphviz python module installed."""
        with pytest.raises(ImportError):
            self.workflow.display()

    def test_display_with_graphviz_module_and_dependency(self):
        """
        Test display method with graphviz python module and graphviz software
        installed
        """
        self.workflow.display()

    @mock.patch('fairworkflows.rdf_wrapper.NanopubClient.publish')
    def test_publish_as_nanopub(self, mock_publish):
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
        for step in self.workflow:
            assert step.is_modified
        self.workflow.publish_as_nanopub()
        assert mock_publish.call_count == 4  # 1 workflow, 3 steps
        for step in self.workflow:
            assert step.uri in test_published_uris
            assert ((rdflib.URIRef(step.uri), None, None) in self.workflow.rdf
                    or (None, None, rdflib.URIRef(step.uri)) in self.workflow.rdf), \
                'The new step URIs are not in the workflow'
        for uri in self.test_step_uris:
            assert ((rdflib.URIRef(uri), None, None) not in self.workflow.rdf
                    and (None, None, rdflib.URIRef(uri)) not in self.workflow.rdf), \
                'The old step URIs are still in the workflow'

    @mock.patch('fairworkflows.rdf_wrapper.NanopubClient.publish')
    def test_publish_as_nanopub_no_modifications(self, mock_publish):
        """
        Test case of an already published workflow that itself nor its steps are not modified.
        """
        for step in self.workflow:
            step._is_modified = False
        self.workflow._is_modified = False
        self.workflow._is_published = True
        pubinfo = self.workflow.publish_as_nanopub()
        assert mock_publish.call_count == 0
        assert pubinfo['nanopub_uri'] is None
