from core import cwl
import yaml
from pathlib import Path

SAMPLE_STEP = {'name': 'step1',
               'description': 'description of step 1',
               'input': ['sample_input1', 'sample_input2'],
               'output': ['sample_output']}

WORKFLOW_NAME = 'test_workflow'


def test_sample_step_generates_sample_commandlinetool():
    tool_dict = cwl.create_commandlinetool(SAMPLE_STEP).get_dict()

    target = {'cwlVersion': 'v1.0', 'id': 'step1',
              'inputs': [{'id': 'sample_input1', 'type': 'int'},
                         {'id': 'sample_input2', 'type': 'int'}],
              'outputs': [{'id': 'sample_output', 'type': 'int'}],
              'baseCommand': './step1.py',
              'doc': 'description of step 1',
              'class': 'CommandLineTool'}

    assert target == tool_dict


def test_sample_workflow_has_one_step(tmp_path):
    project_dir = Path(tmp_path) / WORKFLOW_NAME
    if not project_dir.exists():
        project_dir.mkdir()

    result_path = cwl.create_workflow(WORKFLOW_NAME, [SAMPLE_STEP], project_dir)

    with result_path.open('r') as f:
        wf = yaml.load(f)

        assert 1 == len(wf['steps'])
