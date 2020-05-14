import logging
import tempfile
from pathlib import Path
from typing import List, Union, Dict, Optional
import tempfile
from toil.cwl import cwltoil

from .exceptions import CWLException

_logger = logging.getLogger(__name__)

DEFAULT_TYPE = 'int'
PROVENANCE = 'provenance'

def run_workflow(wf_path: Union[Path, str], inputs: Dict[str, any], output_dir: Optional[Union[Path, str]] = None,
                 base_dir=None):
    _logger.debug(f'Running CWL tool at {wf_path}')
    _logger.debug(f'Input values: {inputs}')
    _logger.debug(f'Results will be written to {output_dir}')

    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp())
    log_path = str(output_dir / 'log.txt')
    prov_dir = output_dir / PROVENANCE

    wf_path = str(wf_path)

    wf_input = [f'--{k}={v}' for k, v in inputs.items()]

    cwltool_args = []

    if base_dir:
        cwltool_args += ['--basedir', str(base_dir)]

    cwltool_args += ['--logFile', str(log_path)]
    cwltool_args += ['--outdir', str(output_dir)]

    # RO Crate containing provenance will be stored in a "provenance" subdirectory
    cwltool_args += ['--provenance', str(prov_dir)]

    try:
        cwltoil.main(cwltool_args + [wf_path] + wf_input)
    except SystemExit as e:
        raise CWLException(f'Workflow {wf_path} with inputs {inputs} has failed.', e)

    _logger.debug('CWL tool has run successfully.')

    with open(log_path, 'r') as infile:
        runlogs = infile.read()

    return output_dir, runlogs
