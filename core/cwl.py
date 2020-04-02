from pathlib import Path
from typing import List, Union, Dict

import cwlgen
from scriptcwl import WorkflowGenerator


def create_workflow(name, steps, steps_dir, working_dir: Union[str, Path]):
    steps_dir = str(steps_dir)
    with WorkflowGenerator(steps_dir, working_dir) as wf:
        wf.load(steps_dir)

        filepath = Path(working_dir) / f'{name}.cwl'

        filepath.write_text(script)


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
