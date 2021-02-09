import inspect
import typing
from typing import List, get_type_hints

from fairworkflows import FairVariable
from fairworkflows.config import IS_FAIRSTEP_RETURN_VALUE_PARAMETER_NAME


def extract_inputs_from_function(func, additional_params) -> List[FairVariable]:
    """
    Extract inputs from function using inspection. The name of the argument will be the name of
    the fair variable, the corresponding type hint will be the type of the variable.
    """
    argspec = inspect.getfullargspec(func)
    try:
        return [FairVariable(
                    name=arg,
                    computational_type=argspec.annotations[arg].__name__,
                    semantic_types=additional_params.get(arg))
                    for arg in argspec.args]
    except KeyError:
        raise ValueError('Not all input arguments have type hinting, '
                         'FAIR step functions MUST have type hinting, '
                         'see https://docs.python.org/3/library/typing.html')


def extract_outputs_from_function(func, additional_params) -> List[FairVariable]:
    """
    Extract outputs from function using inspection. The name will be {function_name}_output{
    output_number}. The corresponding return type hint will be the type of the variable.
    """
    annotations = get_type_hints(func)
    try:
        return_annotation = annotations['return']
    except KeyError:
        raise ValueError('The return of the function does not have type hinting, '
                         'FAIR step functions MUST have type hinting, '
                         'see https://docs.python.org/3/library/typing.html')
    if _is_generic_tuple(return_annotation):
        return_sem_types = additional_params.get(IS_FAIRSTEP_RETURN_VALUE_PARAMETER_NAME)
        if return_sem_types is not None:
            num_return_args = len(return_annotation.__args__)
            if len(return_sem_types) != num_return_args:
                raise ValueError(f'"out" parameter to is_fairstep decorator must be a '
                                  'tuple of length number of returned values (in this case, '
                                  '{num_return_args}).')
        else:
            return_sem_types = [None for arg in return_annotation.__args__]

        return [FairVariable(
                    name='out' + str(i + 1),
                    computational_type=annotation.__name__,
                    semantic_types=return_sem_types[i])
                for i, annotation in enumerate(return_annotation.__args__)]
    else:
        return [FairVariable(
                name='out1',
                computational_type=return_annotation.__name__,
                semantic_types=additional_params.get(IS_FAIRSTEP_RETURN_VALUE_PARAMETER_NAME))]


def _is_generic_tuple(type_):
    """
    Check whether a type annotation is Tuple
    """
    if hasattr(typing, '_GenericAlias'):
        # 3.7
        # _GenericAlias cannot be imported from typing, because it doesn't
        # exist in all versions, and it will fail the type check in those
        # versions as well, so we ignore it.
        return (isinstance(type_, typing._GenericAlias)
                and type_.__origin__ is tuple)
    else:
        # 3.6 and earlier
        # GenericMeta cannot be imported from typing, because it doesn't
        # exist in all versions, and it will fail the type check in those
        # versions as well, so we ignore it.
        return (isinstance(type_, typing.GenericMeta)
                and type_.__origin__ is typing.Tuple)
