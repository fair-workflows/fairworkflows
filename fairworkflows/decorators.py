from .fairstep import FairStep
from .fairworkflow import FairWorkflow

def fairstep(fw:FairWorkflow):
    """
    Decorator that, upon execution, will convert a function to a FairStep, and add it to the
    given FairWorkflow, 'fw'
    """

    def decorated_step(function):

        def wrapped_step(*args, **kwargs):
            fw.add(FairStep.from_function(function=function))
            function(*args, **kwargs)

        return wrapped_step

    return decorated_step
