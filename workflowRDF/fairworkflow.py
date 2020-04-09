import os
import rdflib
from rdflib.namespace import RDF, RDFS, DC, XSD, OWL 
import inspect
from datetime import datetime

PPLAN = rdflib.Namespace("http://purl.org/net/p-plan#")
EDAM = rdflib.Namespace("http://edamontology.org/")
PROV = rdflib.Namespace("http://www.w3.org/ns/prov#")
DUL = rdflib.Namespace("http://ontologydesignpatterns.org/wiki/Ontology:DOLCE+DnS_Ultralite/")
BPMN = rdflib.Namespace("https://www.omg.org/spec/BPMN/")
PWO = rdflib.Namespace("http://purl.org/spar/pwo/")
RDFG = rdflib.Namespace("http://www.w3.org/2004/03/trix/rdfg-1/")
NP = rdflib.Namespace("http://www.nanopub.org/nschema#")

class FairWorkflow:
    def __init__(self, name='newworkflow'):
        self.THISWORKFLOW = rdflib.Namespace("http://purl.org/nanopub/temp/FAIRWorkflowsTest/workflow/")
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
        rdf.bind("edam", EDAM)
        rdf.bind("prov", PROV)
        rdf.bind("dul", DUL)
        rdf.bind("bpmn", BPMN)
        rdf.bind("pwo", PWO)
        rdf.bind("rdfg", RDFG)
        rdf.bind("np", NP)

        # Add steps metadata
        if len(self.steps) > 0:

            # Workflow metadata
            first_step = self.steps[0]
            rdf.add( (self.THISWORKFLOW[''], RDF.type, DUL.workflow) )
            rdf.add( (self.THISWORKFLOW[''], PWO.hasFirstStep, first_step.THISSTEP['']) )

            # Add metadata from all the steps to this rdf graph
            for step in self.steps:
                rdf.add((step.THISSTEP[''], PPLAN.isStepOfPlan, self.THISWORKFLOW['']))

                for var, arg in zip(step.func.__code__.co_varnames, step.args):
                    if isinstance(arg, FairStepEntry):
                        rdf.add((step.THISSTEP[var], PPLAN.isOutputVarOf, arg.THISSTEP['']))
                        rdf.add((arg.THISSTEP[''], DUL.precedes, step.THISSTEP['']))
                    else:
                        binding = self.THISWORKFLOW[var + '#' + str(arg)]
                        rdf.add((self.THISWORKFLOW[var], PROV.qualifiedUsage, binding))
                        rdf.add((binding, RDF.type, PROV.Usage))
                        rdf.add((binding, PROV.entity, self.THISWORKFLOW[var]))
                        rdf.add((binding, RDF.value, rdflib.Literal(f'{str(arg)}')))
        return rdf

    def __str__(self):
        return self.get_rdf().serialize(format='turtle').decode("utf-8")

    def rdf_to_file(self, fname, format='turtle'):
        return self.get_rdf().serialize(destination=fname, format=format)
        
    def nanopublish(self, url=None):
        for step in self.steps:
            step.nanopublish(url=url)

class FairStepEntry:
    def __init__(self, func, args, kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.executed = False
        self.result = None

        self.np_uri = "http://purl.org/nanopub/temp/FAIRWorkflowsTest/Step"
        self.THISNP = rdflib.Namespace(self.np_uri)
        self.THISSTEP = rdflib.Namespace(self.np_uri + '/' + func.__name__ + '/')

    def nanopublish(self, url=None):
        SUB = rdflib.Namespace(self.np_uri+"/")

        # Set up different contexts
        np_rdf = rdflib.ConjunctiveGraph()
        head = rdflib.Graph(np_rdf.store, SUB.Head)
        assertion = rdflib.Graph(np_rdf.store, SUB.assertion)
        provenance = rdflib.Graph(np_rdf.store, SUB.provenance)
        pubInfo = rdflib.Graph(np_rdf.store, SUB.pubInfo)

        np_rdf.bind("this", self.THISNP)
        np_rdf.bind("sub", SUB)
        np_rdf.bind("np", NP)

        np_rdf.bind("p-plan", PPLAN)
        np_rdf.bind("edam", EDAM)
        np_rdf.bind("prov", PROV)
        np_rdf.bind("dul", DUL)
        np_rdf.bind("bpmn", BPMN)
        np_rdf.bind("pwo", PWO)
        np_rdf.bind("rdfg", RDFG)

        head.add((self.THISNP[''], RDF.type, NP.Nanopublication))
        head.add((self.THISNP[''], NP.hasAssertion, SUB.assertion))
        head.add((self.THISNP[''], NP.hasProvenance, SUB.provenance))
        head.add((self.THISNP[''], NP.hasPublicationInfo, SUB.pubInfo))

        assertion += self.generate_step_rdf()

        creationtime = rdflib.Literal(datetime.now(),datatype=XSD.date)
        provenance.add((SUB.assertion, PROV.generatedAtTime, creationtime))
        provenance.add((SUB.assertion, PROV.wasDerivedFrom, self.THISNP.experiment)) 
        provenance.add((SUB.assertion, PROV.wasAttributedTo, self.THISNP.experimentScientist))

        pubInfo.add((self.THISNP[''], PROV.wasAttributedTo, self.THISNP.DrBob))
        pubInfo.add((self.THISNP[''], PROV.generatedAtTime, creationtime))

        # Convert nanopub rdf to trig
        stepname = str(self.func.__name__)
        fname = f'step_{stepname}.trig'
        serialized = np_rdf.serialize(destination=fname, format='trig')

        # Sign the nanopub and publish it
        os.system('np sign ' + fname)
        signed_fname = 'signed.' + fname
        #os.system('np publish ' + signed_fname)

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

    def generate_step_rdf(self):

        # Autogenerate rdf metadata for this step
        rdf = rdflib.Graph()

        rdf.add((self.THISSTEP[''], RDF.type, PPLAN.Step))
        rdf.add((self.THISSTEP[''], RDF.type, BPMN.scriptTask))

        for var, arg in zip(self.func.__code__.co_varnames, self.args):
            rdf.add((self.THISSTEP[var], RDF.type, PPLAN.Variable))
            rdf.add((self.THISSTEP[''], PPLAN.hasInputVar, self.THISSTEP[var]))

        # Grab entire function's source code for step 'description'
        func_src = inspect.getsource(self.func)
        rdf.add((self.THISSTEP[''], DC.description, rdflib.Literal(func_src)))

        return rdf

 

    def __str__(self):
        return self.get_rdf().serialize(format='turtle').decode("utf-8")


def FairStep(fairworkflow):
    def fair_wrapper(func):
        def metadata_wrapper(*args, **kwargs):

            # Add the new step to the workflow
            fairstep = FairStepEntry(func, args, kwargs)
            fairworkflow.add_step(fairstep)

            return fairstep
        return metadata_wrapper
    return fair_wrapper
