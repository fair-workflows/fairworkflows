from scriptcwl import WorkflowGenerator
from pathlib import Path


def create_workflow(name, steps_dir, working_dir):
    steps_dir = str(steps_dir)
    wf_gen = WorkflowGenerator(steps_dir, working_dir)
    script = wf_gen.to_script(name)

    filepath = Path(working_dir) / f'{name}.cwl'

    filepath.write_text(script)
