import os
from pathlib import Path
from typing import Union

import rdflib

ROOT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
NANOPUB_SCRIPT = str(ROOT_DIR/'np')

def sign(unsigned_file: Union[str]) -> str:
    os.system(f'{NANOPUB_SCRIPT} sign ' + unsigned_file)

    return _get_signed_file(unsigned_file)


def publish(signed: str):
    os.system(f'{NANOPUB_SCRIPT} publish ' + signed)

    return extract_nanopub_url(signed)


def extract_nanopub_url(signed):
    # Extract nanopub URL
    # (this is pretty horrible, switch to python version as soon as it is ready)
    extracturl = rdflib.Graph()
    extracturl.parse(signed, format="trig")
    return dict(extracturl.namespaces())['this'].__str__()


def _get_signed_file(unsigned_file: str):
    unsigned_file = Path(unsigned_file)

    return str(unsigned_file.parent / f'signed.{unsigned_file.name}')
