from .fairstep import FairStep
from .fairworkflow import FairWorkflow

def fairstep(fw:FairWorkflow):

    def decorated_step(func):

        def wrapped_step(*args, **kwargs):
            fw.add(FairStep(func=func))
            func(*args, **kwargs)

        return wrapped_step

    return decorated_step
