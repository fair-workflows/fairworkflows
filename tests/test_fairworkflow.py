import pytest
import requests

from fairworkflows import FairWorkflow, FairStep

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

