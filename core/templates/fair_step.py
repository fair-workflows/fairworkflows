#!/usr/bin/env python3

import click

@click.command(){% for arg in input %}
@click.option('--{{arg}}'){% endfor %}
def {{name}}({{input|join(', ')}}):
    '''
    {{description}}
    '''
    pass


if __name__ == '__main__':
    {{name}}()
