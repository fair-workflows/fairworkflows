""" Generate sample workflow

This module is for generating a workflow to see what the result looks like without having to go through the prompts
each time.
"""

import shutil
from pathlib import Path

from core import workflow

RESULTS_DIR = 'sample_output'
WORKFLOW_NAME = 'sample_workflow'
WORKFLOW_STEPS = [{'name': 'step1', 'description': 'description of step 1', 'input': ['sample_input1', 'sample_input2'],
                   'output': ['sample_output']},
                  {'name': 'step2', 'description': 'description of step 2', 'input': ['sample_input1', 'sample_input2'],
                   'output': ['sample_output']}
                  ]


def main():
    results_path = Path.cwd() / RESULTS_DIR

    if results_path.exists():
        shutil.rmtree(results_path)

    results_path.mkdir()

    workflow.process_workflow(WORKFLOW_NAME, WORKFLOW_STEPS, results_path)


if __name__ == '__main__':
    main()
