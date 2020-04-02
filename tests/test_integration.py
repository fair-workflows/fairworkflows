from core import workflow
import pytest
SAMPLE_STEPS = [{'name': 'step1', 'description': 'This is the first step', 'inputs': ['a', 'b'], 'output': ['result']}]
WORKFLOW_NAME = 'test_workflpw'
TARGET_DIR = 'integration_test_workflow'


def test_process_workflow_doesnt_fail(tmp_path):
    try:
        workflow.process_workflow(WORKFLOW_NAME, SAMPLE_STEPS, tmp_path)
    except:
        pytest.fail('Processing workflow failed')

    assert True
