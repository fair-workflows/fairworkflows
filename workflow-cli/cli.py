#!/usr/bin/env python3
from pathlib import Path
from typing import List, Dict
import pythongen
import rdf
import click
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(loader=FileSystemLoader('templates'),
                  autoescape=select_autoescape('py'))


@click.group('cli')
def cli():
    pass


@click.command()
@click.option('--name', prompt='Name of the workflow')
@click.option('--target', prompt='Target directory')
def create_workflow(name, target):
    """
    Create a new workflow interactively.
    @param name:
    @param target:
    """
    print('Let\'s define the steps!')
    steps = prompt_continuous(['name', 'description', 'input', 'output'])

    template = env.get_template('fair_step.py')

    # TODO: Add option to specify target dir
    workflow_dir = Path(target) / name

    workflow_dir.mkdir()

    pythongen.render_python_workflow(steps, template, workflow_dir)

    plex_file = workflow_dir / f'{name}.plex'
    plex_workflow = _create_plex_workflow(name, steps)
    plex_workflow.render(str(plex_file))


def _create_plex_workflow(name, steps):
    plex_workflow = rdf.PlexWorkflow(name)
    for step in steps:
        plex_workflow.add_step(step['name'], step['description'])

    return plex_workflow


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
