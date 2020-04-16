import os
from pathlib import Path
from typing import Union

from config import NANOPUB_SCRIPT


def sign(unsigned_file: Union[str]) -> str:
    os.system(f'{NANOPUB_SCRIPT} sign ' + unsigned_file)

    return _get_signed_file(unsigned_file)


def publish(signed: str):
    os.system(f'{NANOPUB_SCRIPT} publish ' + signed)


def _get_signed_file(unsigned_file: str):
    unsigned_file = Path(unsigned_file)

    return str(unsigned_file.parent / f'signed.{unsigned_file.name}')
