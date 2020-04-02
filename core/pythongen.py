from jinja2 import FileSystemLoader, select_autoescape, Environment

import config

TEMPLATE_DIR = config.CORE_DIR / 'templates'

ENV = Environment(loader=FileSystemLoader(TEMPLATE_DIR),
                  autoescape=select_autoescape('py'))

TEMPLATE = ENV.get_template('fair_step.py')


def render_python_workflow(steps, workflow_dir):
    # Store every step in a separate file in the workflow directory
    for step in steps:
        _render_python_step(step, workflow_dir)


def _render_python_step(step, workflow_dir):
    filename = step['name'] + '.py'
    with (workflow_dir / filename).open('w') as f:
        f.write(TEMPLATE.render(**step))
