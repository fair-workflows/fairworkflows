
def render_python_workflow(steps, template, workflow_dir):
    # Store every step in a separate file in the workflow directory
    for step in steps:
        _render_python_step(step, template, workflow_dir)


def _render_python_step(step, template, workflow_dir):
    filename = step['name'] + '.py'
    with (workflow_dir / filename).open('w') as f:
        f.write(template.render(**step))
