from fairworkflows import FairWorkflow, FairStep, fairstep


class TestFairWorkflow:
    test_description = 'This is a test workflow.'
    workflow = FairWorkflow(description=test_description)

    step1 = FairStep(uri='http://www.example.org/step1')
    step2 = FairStep(uri='http://www.example.org/step2')
    step3 = FairStep(uri='http://www.example.org/step3')

    workflow.add(step2, follows=step1)
    workflow.add(step3, follows=step2)
    workflow.set_first_step(step1)

    def test_build(self):
        workflow = FairWorkflow(description=self.test_description)

        assert workflow is not None
        assert str(workflow.description) == self.test_description

        assert not workflow.validate()

        workflow.add(self.step2, follows=self.step1)
        workflow.add(self.step3, follows=self.step2)

        assert not workflow.validate()

        workflow.set_first_step(self.step1)

        assert workflow.validate()

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

        assert workflow.validate() is False

        test_fn(1, 2)

        assert workflow.validate() is True

    def test_draw(self, tmp_path):
        # Check for errors when calling draw()...
        self.workflow.draw(filepath=str(tmp_path))

    def test_display(self):
        self.workflow.display()
