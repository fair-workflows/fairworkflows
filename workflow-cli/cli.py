#!/usr/bin/env python3

import click
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(loader=FileSystemLoader('templates'),
                  autoescape=select_autoescape('py'))


@click.group('cli')
def cli():
    pass


@click.command()
@click.option('--name', prompt='Name of the workflow')
def create_workflow(name):
    steps = []
    # Prompt for steps
    while True:
        step_name = input('Name your step: ')
        if (step_name is None) or step_name == '':
            break

        step_description = input(f'What does {step_name} do? ')
        steps.append({'name': step_name, 'description': step_description})

    template = env.get_template('FairWorkflow.py')
    with open(f'{name}.py', 'w') as f:
        f.write(template.render(workflow_name=name, steps=steps))


cli.add_command(create_workflow)

if __name__ == '__main__':
    cli()
