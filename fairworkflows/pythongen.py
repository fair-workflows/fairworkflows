from pathlib import Path

from jinja2 import FileSystemLoader, select_autoescape, Environment

from fairworkflows import config
from fairworkflows.config import PYTHON_DIR

TEMPLATE_DIR = config.PACKAGE_DIR / 'templates'

ENV = Environment(loader=FileSystemLoader(TEMPLATE_DIR),
                  autoescape=select_autoescape('py'))

TEMPLATE = ENV.get_template('fair_step.py')


def render_python_workflow(steps, project_dir):
    target_dir = Path(project_dir) / PYTHON_DIR

    if not target_dir.exists():
        target_dir.mkdir()

    # Store every step in a separate file in the workflow directory
    for step in steps:
        filepath = _render_python_step(step, target_dir)
        step['code'] = filepath


def _render_python_step(step, workflow_dir):
    filename = step['name'] + '.py'
    target = workflow_dir / filename
    with target.open('w') as f:
        f.write(TEMPLATE.render(**step))

    return target
