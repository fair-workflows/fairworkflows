class RDFtriple:
    def __init__(self, sub, pred, obj):
        self.sub = sub
        self.pred = pred
        self.obj = obj

    def __str__(self):
        return '  '.join([self.sub, self.pred, self.obj])


class FairWorkflow:
    def __init__(self, name='newworkflow'):
        self.name = 'plex:' + name
        self.steps = []

    def add_step(self, fairstep):
        self.steps.append(fairstep)

    def execute(self):
        running = True
        while running:
            for step in self.steps:
                running = False
                if step.execute() is False:
                    running = True

        return self.steps[-1].get_result()

    def __str__(self):
        """
            Build RDF metadata for entire FAIR Workflow
        """
        meta = ''
        if len(self.steps) > 0:

            # Prefix header
            meta += "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n"
            meta += "@prefix p-plan: <http://purl.org/net/p-plan#>\n"
            meta += "@prefix plex <https://github.com/perma-id/w3id.org/tree/master/fair/plex>\n"
            meta += "@prefix edam <http://edamontology.org/>\n"
            meta += "@prefix prov: <http://www.w3.org/ns/prov#>\n"
            meta += "@prefix dul: <http://ontologydesignpatterns.org/wiki/Ontology:DOLCE+DnS_Ultralite>\n"
            meta += "@prefix bpmn <https://www.omg.org/spec/BPMN/>\n"
            meta += "\n"

            # Workflow metadata
            first_step = self.steps[0]
            plan_rdf = []
            plan_rdf.append(RDFtriple(self.name, 'rdf:type', 'dul:workflow'))
            plan_rdf.append(RDFtriple(self.name, 'pwo:hasFirstStep', first_step.name))
            for var, arg in zip(first_step.func.__code__.co_varnames, first_step.args):
                varname = "plex:" + var
                binding = varname + "#" + str(arg)
                plan_rdf.append(RDFtriple(self.name, "prov:qualifiedUsage", binding))
                plan_rdf.append(RDFtriple(binding, "rdf:type", "prov:Usage"))
                plan_rdf.append(RDFtriple(binding, "prov:entity", varname))
                plan_rdf.append(RDFtriple(binding, "rdf:value", f'"{str(arg)}"^^xsd:{str(type(arg))}'))

            meta += '\n'.join([str(s) for s in plan_rdf]) + '\n\n'

            # Steps metadata
            meta += "\n".join([str(s) for s in self.steps]) + '\n'

        return meta


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
    def fair_wrapper(func):
        def metadata_wrapper(*args, **kwargs):

            # Autogenerate metadata
            metadata = []

            stepname = "plex:" + func.__name__

            metadata.append(RDFtriple(stepname, "rdf:type", "p-plan:Step"))
            metadata.append(RDFtriple(stepname, "rdf:type", "bpmn:scriptTask"))
            metadata.append(RDFtriple(stepname, "p-plan:isStepOfPlan", fairworkflow.name))
            
            for var, arg in zip(func.__code__.co_varnames, args):
                metadata.append(RDFtriple('plex:' + var, 'rdf:type', 'p-plan:Variable'))
                metadata.append(RDFtriple(stepname, "p-plan:hasInputVar", 'plex:' + var))

                if isinstance(arg, FairStepEntry):
                    metadata.append(RDFtriple('plex:' + var, "p-plan:isOutputVarOf", arg.name))
                    metadata.append(RDFtriple(arg.name, "dul:precedes", stepname))

            if func.__doc__:
                metadata.append(RDFtriple(stepname, "dc:description", f'"{func.__doc__.strip()}"'))

            fairstep = FairStepEntry(stepname, func, args, kwargs, metadata)

            fairworkflow.add_step(fairstep)

            return fairstep
        return metadata_wrapper
    return fair_wrapper
