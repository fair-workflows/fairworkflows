from unittest.mock import patch

from core import workflow
import pytest

SAMPLE_STEPS = [{'name': 'step1', 'description': 'This is the first step', 'input': ['a', 'b'], 'output': ['result']},
                {'name': 'step2', 'description': 'This is the second step', 'input': ['result'],
                 'output': ['final_result']}]
WORKFLOW_NAME = 'test_workflow'
TARGET_DIR = 'integration_test_workflow'
MOCK_URI = 'http://sample.com/sample'


def test_process_workflow_doesnt_fail(tmp_path):
    with patch('core.nanopub.nanopub.wrapper') as mock_wrapper:
        mock_wrapper.sign.return_value = 'signed.test.something'
        mock_wrapper.publish.return_value = MOCK_URI
        workflow.process_workflow(WORKFLOW_NAME, SAMPLE_STEPS, tmp_path)

        assert True
