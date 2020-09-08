from unittest import mock

import pytest

from fairworkflows import FairWorkflow, FairStep, fairstep


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

    def test_iterator(self):
        """Test iterating over the workflow."""
        right_order_steps = [self.step1, self.step2, self.step3]
        workflow_steps = list(self.workflow)
        assert len(workflow_steps) == len(right_order_steps)
        for i, step in enumerate(workflow_steps):
            assert step == right_order_steps[i]

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

