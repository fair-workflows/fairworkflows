class FairWorkflow:
    def __init__(self, name='newworkflow'):
        self.name = 'plex:' + name
        self.flow = []

    def add_step(self, fairstep):
        self.flow.append(fairstep)

    def execute(self):
        running = True
        while running:
            for step in self.flow:
                running = False
                if step.execute() is False:
                    running = True

        return self.flow[-1].get_result()

    def __str__(self):
        return "\n".join([str(s) for s in self.flow])

class RDFtriple:
    def __init__(self, sub, pred, obj):
        self.sub = sub
        self.pred = pred
        self.obj = obj

    def __str__(self):
        return '  '.join([self.sub, self.pred, self.obj])

class FairStepEntry:
    def __init__(self, name, func, args, kwargs, metadata):
        self.name = name
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.metadata = metadata
        self.executed = False
        self.result = None

    def execute(self):
        resolved_args = []
        for a in self.args:
            if isinstance(a, FairStepEntry):
                if a.has_executed():
                    resolved_args.append(a.get_result())
                else:
                    return False
            else:
                resolved_args.append(a)
                
        self.result = self.func(*resolved_args, **self.kwargs)
        print("executing " + self.name)

        self.executed = True

        return True
    
    def has_executed(self):
        return self.executed

    def get_result(self):
        return self.result

    def __str__(self):
        metastr = '\n'.join([str(s) for s in self.metadata])
        return f"{metastr}\n"

def FairStep(fairworkflow):
    def fairdecorator(func):
        def wrappedfn(*args, **kwargs):

            # Autogenerate metadata
            metadata = []

            stepname = "plex:" + func.__name__

            metadata.append(RDFtriple(stepname, "rdf:type", "p-plan:Step"))
            metadata.append(RDFtriple(stepname, "rdf:type", "bpmn:scriptTask"))
            metadata.append(RDFtriple(stepname, "p-plan:isStepOfPlan", fairworkflow.name))
            
            for var, arg in zip(func.__code__.co_varnames, args):
                metadata.append(RDFtriple(stepname, "p-plan:hasInputVar", 'plex:' + var))

                if isinstance(arg, FairStepEntry):
                    metadata.append(RDFtriple('plex:' + var, "p-plan:isOutputVarOf", arg.name))

            if func.__doc__:
                metadata.append(RDFtriple("description", func.__doc__.strip()))

            fairstep = FairStepEntry(stepname, func, args, kwargs, metadata)

            fairworkflow.add_step(fairstep)

            return fairstep
        return wrappedfn
    return fairdecorator
