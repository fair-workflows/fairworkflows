from core import cwl

SAMPLE_STEP = {'name': 'step1',
               'description': 'description of step 1',
               'input': ['sample_input1', 'sample_input2'],
               'output': ['sample_output']}


def test_sample_step_generates_sample_commandlinetool():
    tool_dict = cwl.create_commandlinetool(SAMPLE_STEP).get_dict()

    target = {'cwlVersion': 'v1.0', 'id': 'step1', 'inputs': [{'id': 'sample_input1'}, {'id': 'sample_input2'}],
              'outputs': [{'id': 'sample_output'}], 'baseCommand': './step1.py', 'doc': 'description of step 1',
              'class': 'CommandLineTool'}

    assert target == tool_dict
