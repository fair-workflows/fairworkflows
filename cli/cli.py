#!/usr/bin/env python3

from typing import List, Dict

import click

from core.workflow import process_workflow

SCRIPTS = 'scripts'
PLEX = 'plex'
CWL = 'cwl'


@click.group('cli')
def cli():
    pass


@click.command()
@click.option('--name', prompt='Name of the workflow')
@click.option('--target', prompt='Target directory')
def create_workflow(name, target):
    """
        Create a new workflow interactively.
    :param name:
    :param target:
    :return:
    """
    print('Let\'s define the steps!')
    steps = prompt_continuous(['name', 'description', 'input', 'output'])

    # Inputs and outputs have multiple values separated by commas
    for step in steps:
        step['input'] = step['input'].split(',')
        step['output'] = step['output'].split(',')

    process_workflow(name, steps, target)


def prompt_continuous(questions: List[str]) -> List[Dict[str, str]]:
    """
    Contiuously prompts for a list of questions until the user doesn't specify an answer anymore.
    :param questions:
    :return:
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


def main():
    cli()
