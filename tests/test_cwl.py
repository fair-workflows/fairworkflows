import pytest

from fairworkflows.config import TESTS_RESOURCES
from fairworkflows import cwl
from fairworkflows.exceptions import CWLException

SAMPLE_CWL_TOOL = TESTS_RESOURCES / 'test_flow.cwl'


def test_run_workflow_produces_result(tmp_path):
    cwl.run_workflow(SAMPLE_CWL_TOOL, {'message': 'greetings'}, tmp_path)

    result = (tmp_path / 'output.txt').read_text()

    assert 'greetings' == result.strip()


def test_missing_mandatory_input_raises_exception():
    with pytest.raises(CWLException):
        cwl.run_workflow(SAMPLE_CWL_TOOL, {})


def test_run_workflow_produces_provenance(tmp_path):
    cwl.run_workflow(SAMPLE_CWL_TOOL, {'message': 'Provenance will be recorded for this'}, output_dir=tmp_path)
    prov_path = tmp_path/'provenance'

    assert prov_path.exists()
    assert len(list(prov_path.iterdir())) > 0
