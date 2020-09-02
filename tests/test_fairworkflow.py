import pytest
import requests

from fairworkflows import FairWorkflow, FairStep, fairstep

def test_build_fairworkflow():
    workflow = FairWorkflow(description='This is a test workflow.')

    assert(workflow is not None)
    assert(workflow.description() is not None)

    step1 = FairStep(uri='http://www.example.org/step1')
    step2 = FairStep(uri='http://www.example.org/step2')
    step3 = FairStep(uri='http://www.example.org/step3')

    workflow.add(step2, follows=step1)
    workflow.add(step3, follows=step2)

    assert(workflow.validate() is False)

    workflow.set_first_step(step1)

    assert(workflow.validate() is True)

    assert(workflow.__str__() is not None)
    assert(len(workflow.__str__()) > 0)
    assert(workflow.rdf is not None)

    # Now test plex iterator of the workflow
    steps = [step1, step2, step3]
    i = 0
    for step in workflow:
        assert(step.uri == steps[i].uri)
        i += 1

def test_decorator():
    workflow = FairWorkflow(description='This is a test workflow.')

    @fairstep(workflow)
    def test_fn(x, y):
        return x * y

    assert(workflow.validate() is False)

    test_fn(1, 2)

    assert(workflow.validate() is True)
    
