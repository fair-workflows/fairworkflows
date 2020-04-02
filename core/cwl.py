from pathlib import Path
from typing import List, Union, Dict

import cwlgen
from scriptcwl import WorkflowGenerator

DEFAULT_TYPE = 'str'


def create_workflow(name, steps, steps_dir, working_dir: Union[str, Path]):
    steps_dir = str(steps_dir)
    with WorkflowGenerator(steps_dir, working_dir) as wf:
        wf.load(steps_dir)

        # TODO: Replace use of default type with actual specified type
        # Input to the first step is the input to the workflow
        first_step = steps[0]
        inputs = [wf.add_input(**{name: DEFAULT_TYPE}) for name in first_step['inputs']]

        for step in steps:
            step_func = wf.steps_library.get_step(step['name'])
            inputs = step_func(*inputs)

        # Last created inputs are actually the outputs of the worflow
        outputs = inputs

        # The following will fail
        wf.add_outputs(*outputs)

        filepath = Path(working_dir) / f'{name}.cwl'

        wf.save(filepath)


def create_commandlinetool(step: Dict[str, Union[str, List]]) -> cwlgen.CommandLineTool:
    name = step['name']
    description = step['description']

    # Initialize commandlinetool
    # TODO: Specify path
    tool_object = cwlgen.CommandLineTool(tool_id=name,
                                         base_command=f"./{name}.py",
                                         doc=description,
                                         cwl_version="v1.0")

    # Specify input parameters
    tool_object.inputs += [cwlgen.CommandInputParameter(p) for p in step['input']]

    # Specify output parameters
    tool_object.outputs += [cwlgen.CommandInputParameter(p) for p in step['output']]

    return tool_object


def main():
    step = {'name': 'step1', 'description': 'description of step 1', 'input': ['sample_input1', 'sample_input2'],
            'output': ['sample_output']}

    tool = create_commandlinetool(step)

    print(tool.get_dict())


if __name__ == '__main__':
    main()
