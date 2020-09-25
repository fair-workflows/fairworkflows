from unittest import mock

import pytest
import rdflib

from fairworkflows import FairWorkflow, FairStep, fairstep
from fairworkflows.config import TESTS_RESOURCES


class TestFairWorkflow:
    test_description = 'This is a test workflow.'
    workflow = FairWorkflow(description=test_description)

    step1 = FairStep(uri='http://www.example.org/step1')
    step2 = FairStep(uri='http://www.example.org/step2')
    step3 = FairStep(uri='http://www.example.org/step3')

    workflow.first_step = step1
    workflow.add(step2, follows=step1)
    workflow.add(step3, follows=step2)

    def test_build(self):
        workflow = FairWorkflow(description=self.test_description)

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

    def test_construct_from_rdf(self):
        rdf = rdflib.Graph()
        rdf.parse(str(TESTS_RESOURCES / 'test_workflow_including_steps.trig'),
                  format='trig')
        uri = 'http://www.example.org/workflow1'
        workflow = FairWorkflow.from_rdf(rdf, uri)
        valid_step_uris = [uri + '#step1', uri + '#step2', uri + '#step3']
        steps = list(workflow)
        assert len(steps) == 3
        for step in steps:
            step.validate()
            assert step.uri in valid_step_uris
        workflow.validate()

    def test_iterator(self):
        """Test iterating over the workflow."""
        right_order_steps = [self.step1, self.step2, self.step3]
        workflow_steps = list(self.workflow)
        assert len(workflow_steps) == len(right_order_steps)
        for i, step in enumerate(workflow_steps):
            assert step == right_order_steps[i]

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

    @mock.patch('fairworkflows.nanopub_wrapper.publish')
    def test_publish(self, nanopub_wrapper_publish_mock):
        """
        Test (mock) publishing of workflow
        """
        self.workflow.publish_as_nanopub()

    def test_decorator(self):
        workflow = FairWorkflow(description='This is a test workflow.')

        @fairstep(workflow)
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

