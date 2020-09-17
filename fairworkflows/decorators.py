from .fairstep import FairStep
from .fairworkflow import FairWorkflow

def fairstep(fw:FairWorkflow):
    """
    Decorator that, upon execution, will convert a function to a FairStep, and add it to the
    given FairWorkflow, 'fw'
    """

    def decorated_step(func):

        def wrapped_step(*args, **kwargs):
            fw.add(FairStep.from_function(func=func))
            func(*args, **kwargs)

        return wrapped_step

    return decorated_step
