import warnings

import pytest

from fairworkflows import FairWorkflow, FairStep, fairstep, Nanopub


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

    def test_overwrite_first_step(self):
        # First step should be step 1
        assert str(self.workflow.first_step) == self.step1.uri

        # Reset first step to step 2
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self.workflow.first_step = self.step2
            assert len(w) == 1
            assert issubclass(w[-1].category, UserWarning)

        assert str(self.workflow.first_step) == self.step2.uri

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

    def test_draw(self):
        # Check for errors when calling draw()...
        self.workflow.draw(show=False)
