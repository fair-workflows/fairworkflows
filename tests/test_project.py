import os
import tempfile
import shutil
from unittest.mock import patch
from core import project

CWL = 'cwl'
WORKFLOW = 'workflow'
WORKFLOW_NAME = 'sample_workflow'

SAMPLE_WORKFLOW = '''
#!/usr/bin/env cwl-runner
cwlVersion: v1.0
class: Workflow
inputs:
  in: int
outputs: {}
steps:
  step1:
    run: /steps/path/step1.cwl
    in:
      step1/in: in
    out:
    - step1/out
'''


def test_get_steps():
    with MockFileStructure() as project_path:

        steps = project.get_steps(project_path)

        assert steps.keys() == {'step1'}


class MockFileStructure():
    def __init__(self):
        self.project_dir = tempfile.mkdtemp()

        cwl_dir = os.path.join(self.project_dir, CWL)
        os.mkdir(cwl_dir)

        workflow_dir = os.path.join(cwl_dir, WORKFLOW)
        os.mkdir(workflow_dir)

        self.workflow_file = os.path.join(workflow_dir, f'{WORKFLOW_NAME}.cwl')

        with open(self.workflow_file, 'w') as f:
            f.write(SAMPLE_WORKFLOW)

    def __enter__(self):
        return self.project_dir

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Delete temporary directory
        :return:
        """
        shutil.rmtree(self.project_dir)
