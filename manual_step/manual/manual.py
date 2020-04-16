import click
import json

@click.command()
@click.argument('mode', type=str)
def manual(mode):

    if mode == 'commandline':
#        results_uri = input('Enter URI of results for this manual task:\n')
        results_uri = 'file://example.csv'
    elif mode == 'gui':
        raise NotImplementedError
    else:
        raise NotImplementedError

    click.echo(json.dumps({'results_uri': results_uri}))


if __name__ == '__main__':
    manual()
