import inspect
import textwrap
import os
from pathlib import Path

STEPS_DIR = Path('./steps')

def write_pytool(name=None, code=None, inputs=None):

    # Make a directory to keep the steps in if not already existing
    STEPS_DIR.mkdir(parents=True, exist_ok=True)

    fname = STEPS_DIR / (name + ".py")
    with open(fname, 'w') as out:
        s = "import click\nimport json\n\n"
        s += "@click.command()"
        for arg, typ in inputs.items():
            typ = typ.__name__
            s += f"\n@click.argument('{arg}', type={typ})"
 
        s += '\ndef run(*args, **kwargs):\n'
        indented_code = textwrap.indent(code, prefix='    ').replace('@fairstep', '')
        s += '\n' + indented_code + '\n'
        s += "    click.echo(json.dumps({'answer': " + name + "(*args, **kwargs)}))\n"

        s += "\nif __name__ == '__main__':\n"
        s += "    run()\n"

        out.write(s)

    return os.path.abspath(fname)


def write_cwltool(name=None, code=None, inputs=None, return_type=None):

    # Make a directory to keep the steps in if not already existing
    STEPS_DIR.mkdir(parents=True, exist_ok=True)

    pytool_path = write_pytool(name=name, code=code, inputs=inputs)

    fname = STEPS_DIR / (name + ".cwl")
    with open(fname, 'w') as out:
        s = "#!/usr/bin/env cwl-runner\n"
        s += "cwlVersion: v1.0\n"
        s += "class: CommandLineTool\n"
        s += f'baseCommand: ["python3", "{pytool_path}"]\n'
        s += "inputs:\n"
        i = 0
        for arg, typ in inputs.items():
            i += 1
            s += f'    {arg}:\n'
            s += f'        type: {typ.__name__}\n'
            s += f'        inputBinding:\n'
            s += f'            position: {i}\n'

        s += "\nstdout: cwl.output.json\n"
        s += "\noutputs:\n"
        s += "    answer:\n"
        s += f'        type: {return_type.__name__}\n'

        out.write(s)

    return os.path.abspath(fname)


def fairstep(func):
    """
    Decorator to convert step to an appropriate workflow format (e.g. CWL)
    """

    arginfo = inspect.getfullargspec(func) 

    # Check that all variables provided have been given types
    inputs = {}
    for arg in arginfo.args:
        if arg not in arginfo.annotations:
            raise ValueError(f'Argument {arg} does not have a type annotation.')
        else:
            inputs[arg] = arginfo.annotations[arg]

    # Check that return type is explicitly stated
    if 'return' not in arginfo.annotations:
        raise ValueError(f'Function does not have a return type specified')
    else:
        return_type = arginfo.annotations['return']

    cwltool_path = write_cwltool(name=func.__name__, code=inspect.getsource(func), inputs=inputs, return_type=return_type)

    print('Created cwltool at ', cwltool_path)

    return func
