import argparse
import logging
from io import StringIO
from pathlib import Path
from typing import List, Union, Dict, Optional

import cwlgen
import cwltool.main as cwltool_main
from scriptcwl import WorkflowGenerator

from config import CWL_WORKFLOW_DIR, CWL_STEPS_DIR, CWL_DIR
from .exceptions import CWLException

_logger = logging.getLogger(__name__)

DEFAULT_TYPE = 'int'


def create_workflow(name, steps, project_dir):
    # TODO: Right now all steps will be brand new. In the future it should be possible to specify existing steps
    project_dir = Path(project_dir)
    cwl_path = project_dir / CWL_DIR
    steps_path = project_dir / CWL_STEPS_DIR
    workflow_path = project_dir / CWL_WORKFLOW_DIR

    cwl_path.mkdir(exist_ok=True)
    steps_path.mkdir(exist_ok=True)
    workflow_path.mkdir(exist_ok=True)

    # Create commandlinetool for every step
    for step in steps:
        tool_object = create_commandlinetool(step)
        tool_object.export(steps_path / f'{step["name"]}.cwl')

    with WorkflowGenerator() as wf:
        wf.load(steps_path)

        # TODO: Replace use of default type with actual specified type
        # Input to the first step is the input to the workflow
        first_step = steps[0]
        inputs = {f'{first_step["name"]}/{name}': wf.add_input(**{name: DEFAULT_TYPE}) for name in first_step['input']}

        # Add first defined step. We don't have the information on how separate step inputs and outputs are linked so we
        # can't yet add all steps.
        step_func = wf.__getattr__(first_step['name'])
        inputs = step_func(**inputs)
        wf.add_outputs()

        # TODO: Add functionality to link multiple steps

        filepath = workflow_path / f'{name}.cwl'

        wf.save(filepath)

        return filepath


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
    tool_object.inputs += [cwlgen.CommandInputParameter(p, param_type=DEFAULT_TYPE) for p in step['input']]

    # Specify output parameters
    tool_object.outputs += [cwlgen.CommandInputParameter(p, param_type=DEFAULT_TYPE) for p in step['output']]

    return tool_object


def run_workflow(wf_path: Union[Path, str], inputs: Dict[str, any], output_dir: Optional[Union[Path, str]] = None,
                 base_dir=None):
    _logger.debug(f'Running CWL tool at {wf_path}')
    _logger.debug(f'Input values: {inputs}')
    _logger.debug(f'Results will be written to {output_dir}')

    if output_dir:
        output_dir = str(output_dir)

    wf_path = str(wf_path)
    output = StringIO()
    wf_input = [f'--{k}={v}' for k, v in inputs.items()]

    cwltool_args = []

    if output_dir:
        cwltool_args.append(f'--outdir={output_dir}')

    if base_dir:
        cwltool_args.append(f'--basedir={base_dir}')

    cwltool_args.append(wf_path)

    try:
        exit_code = cwltool_main.main(argsl=cwltool_args + wf_input, logger_handler=logging.StreamHandler(stream=output))
    except Exception as e:
        raise CWLException(f'CWL tool run has failed', e)

    print(output, output.read())

    if exit_code > 0:
        raise CWLException(f'Workflow did not run correctly. Exit code: {exit_code}')

    _logger.debug('CWL tool has run successfully.')
    return output.read()


def _create_cwl_args(d: Dict[any, any]):
    # Convert dict arguments to what they would look like as command line arguments.
    args = [f'--{k}={v}' for k, v in d.items()]

    return argparse.ArgumentParser().parse_args(args)
