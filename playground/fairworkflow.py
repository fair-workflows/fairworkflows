import rdflib
from rdflib.namespace import RDF, DC
import inspect

PPLAN = rdflib.Namespace("http://purl.org/net/p-plan/")
PLEX = rdflib.Namespace("https://plex.org/")
EDAM = rdflib.Namespace("http://edamontology.org/")
PROV = rdflib.Namespace("http://www.w3.org/ns/prov/")
DUL = rdflib.Namespace("http://ontologydesignpatterns.org/wiki/Ontology:DOLCE+DnS_Ultralite/")
BPMN = rdflib.Namespace("https://www.omg.org/spec/BPMN/")
PWO = rdflib.Namespace("http://purl.org/spar/pwo/")


class FairWorkflow:
    def __init__(self, name='newworkflow'):
        self.this_workflow = PLEX[name]
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

    def get_rdf(self):
        """
            Build RDF metadata for entire FAIR Workflow
        """

        # Create an rdf graph to add workflow metadata to.
        rdf = rdflib.Graph()

        # Bind all non-standard prefixes in use
        rdf.bind("p-plan", PPLAN)
        rdf.bind("plex", PLEX)
        rdf.bind("edam", EDAM)
        rdf.bind("prov", PROV)
        rdf.bind("dul", DUL)
        rdf.bind("bpmn", BPMN)

        # Add steps metadata
        if len(self.steps) > 0:

            # Workflow metadata
            first_step = self.steps[0]
            rdf.add( (self.this_workflow, RDF.type, DUL.workflow) )
            rdf.add( (self.this_workflow, PWO.hasFirstStep, first_step.this_step) )
            for var, arg in zip(first_step.func.__code__.co_varnames, first_step.args):
                binding = PLEX[var + '#' + str(arg)]
                rdf.add((PLEX[var], PROV.qualifiedUsage, binding))
                rdf.add((binding, RDF.type, PROV.Usage))
                rdf.add((binding, PROV.entity, PLEX[var]))
                rdf.add((binding, RDF.value, rdflib.Literal(f'{str(arg)}')))

            # Add metadata from all the steps to this rdf graph
            for step in self.steps:
                rdf += step.get_rdf()

        return rdf

    def __str__(self):
        return self.get_rdf().serialize(format='turtle').decode("utf-8")

    def rdf_to_file(self, fname, format='turtle'):
        return self.get_rdf().serialize(destination=fname, format=format)
        

class FairStepEntry:
    def __init__(self, rdf_node, func, args, kwargs, rdf_graph):
        self.this_step = rdf_node
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.rdf = rdf_graph
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
        print("executing " + self.func.__name__)

        self.executed = True

        return True
    
    def has_executed(self):
        return self.executed

    def get_result(self):
        return self.result

    def get_rdf(self):
        return self.rdf

    def __str__(self):
        return self.get_rdf().serialize(format='turtle').decode("utf-8")


def FairStep(fairworkflow):
    def fair_wrapper(func):
        def metadata_wrapper(*args, **kwargs):

            # Autogenerate rdf metadata for this step
            rdf = rdflib.Graph()

            this_step = PLEX[func.__name__]

            rdf.add((this_step, RDF.type, PPLAN.Step))
            rdf.add((this_step, RDF.type, BPMN.scriptTask))
            rdf.add((this_step, PPLAN.isStepOfPlan, fairworkflow.this_workflow))

            for var, arg in zip(func.__code__.co_varnames, args):
                rdf.add((PLEX[var], RDF.type, PPLAN.Variable))
                rdf.add((this_step, PPLAN.hasInputVar, PLEX[var]))

                if isinstance(arg, FairStepEntry):
                    rdf.add((PLEX[var], PPLAN.isOutputVarOf, arg.this_step))
                    rdf.add((arg.this_step, DUL.precedes, this_step))

            # Grab entire function's source code for step 'description'
            func_src = inspect.getsource(func)
            rdf.add((this_step, DC.description, rdflib.Literal(func_src)))

            # Add the new step to the workflow
            fairstep = FairStepEntry(this_step, func, args, kwargs, rdf)
            fairworkflow.add_step(fairstep)

            return fairstep
        return metadata_wrapper
    return fair_wrapper
