import logging
from io import StringIO
from pathlib import Path
from typing import List, Union, Dict, Optional
import tempfile

from .exceptions import CWLException
from toil.cwl import cwltoil

_logger = logging.getLogger(__name__)

DEFAULT_TYPE = 'int'


def run_workflow(wf_path: Union[Path, str], inputs: Dict[str, any], output_dir: Optional[Union[Path, str]] = None,
                 base_dir=None):
    _logger.debug(f'Running CWL tool at {wf_path}')
    _logger.debug(f'Input values: {inputs}')
    _logger.debug(f'Results will be written to {output_dir}')

    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp())
    log_path = str(output_dir / 'log.txt')
    output_dir = str(output_dir)

    wf_path = str(wf_path)

    wf_input = [f'--{k}={v}' for k, v in inputs.items()]

    cwltool_args = []

    if output_dir:
        cwltool_args += ['--outdir', str(output_dir)]

    if base_dir:
        cwltool_args += ['--basedir', str(base_dir)]

    cwltool_args += ['--logFile', str(log_path)]

    try:
        cwltoil.main(cwltool_args + [wf_path] + wf_input)
    except SystemExit as e:
        raise CWLException(f'Workflow {wf_path} with inputs {inputs} has failed.', e)

    _logger.debug('CWL tool has run successfully.')

    with open(log_path, 'r') as infile:
        runlogs = infile.read()

    return runlogs
