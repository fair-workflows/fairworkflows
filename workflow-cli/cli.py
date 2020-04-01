#!/usr/bin/env python3
from pathlib import Path
from typing import List, Dict

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
    """
    Create a new workflow interactively.
    @param name:
    """
    steps = prompt_continuous(['name', 'description'])

    template = env.get_template('fair_step.py')

    # TODO: Add option to specify target dir
    workflow_dir = Path(name)

    workflow_dir.mkdir()

    # Store every step in a separate file in the workflow directory
    for step in steps:
        filename = step['name'] + '.py'
        with (workflow_dir / filename).open('w') as f:
            f.write(template.render(**step))


def prompt_continuous(questions: List[str]) -> List[Dict[str, str]]:
    """
    Contiuously prompts for a list of questions until the user doesn't specify an answer anymore.
    @param questions:
    @return:
    """
    answers = []
    while True:
        individual_answers = {}
        for q in questions:
            answer = input(f'Specify {q}: ')
            if (answer is None) or answer == '':
                break
            individual_answers[q] = answer

        if len(individual_answers.keys()) < len(questions):
            break
        answers.append(individual_answers)

    return answers


cli.add_command(create_workflow)

if __name__ == '__main__':
    cli()
