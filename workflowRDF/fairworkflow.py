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


def nanopublish(assertionrdf=None, uri=None):
    """
    Publish the given rdf as a nanopublication with the given URI
    """

    THISNP = rdflib.Namespace(uri+'#')

    # Set up different contexts
    np_rdf = rdflib.ConjunctiveGraph()
    head = rdflib.Graph(np_rdf.store, THISNP.Head)
    assertion = rdflib.Graph(np_rdf.store, THISNP.assertion)
    provenance = rdflib.Graph(np_rdf.store, THISNP.provenance)
    pubInfo = rdflib.Graph(np_rdf.store, THISNP.pubInfo)

    np_rdf.bind("", THISNP)
    np_rdf.bind("np", NP)

    np_rdf.bind("p-plan", PPLAN)
    np_rdf.bind("edam", EDAM)
    np_rdf.bind("prov", PROV)
    np_rdf.bind("dul", DUL)
    np_rdf.bind("bpmn", BPMN)
    np_rdf.bind("pwo", PWO)
    np_rdf.bind("rdfg", RDFG)

    head.add((THISNP[''], RDF.type, NP.Nanopublication))
    head.add((THISNP[''], NP.hasAssertion, THISNP.assertion))
    head.add((THISNP[''], NP.hasProvenance, THISNP.provenance))
    head.add((THISNP[''], NP.hasPublicationInfo, THISNP.pubInfo))

    assertion += assertionrdf

    creationtime = rdflib.Literal(datetime.now(),datatype=XSD.date)
    provenance.add((THISNP.assertion, PROV.generatedAtTime, creationtime))
    provenance.add((THISNP.assertion, PROV.wasDerivedFrom, THISNP.experiment)) 
    provenance.add((THISNP.assertion, PROV.wasAttributedTo, THISNP.experimentScientist))

    pubInfo.add((THISNP[''], PROV.wasAttributedTo, THISNP.DrBob))
    pubInfo.add((THISNP[''], PROV.generatedAtTime, creationtime))

    # Convert nanopub rdf to trig
    fname = 'temp.trig'
    serialized = np_rdf.serialize(destination=fname, format='trig')

    # Sign the nanopub and publish it
    os.system('np sign ' + fname)
    signed_fname = 'signed.' + fname
#    os.system('np publish ' + signed_fname)

    # Extract nanopub URL
    # (this is pretty horrible, switch to python version as soon as it is ready)
    extracturl = rdflib.Graph()
    extracturl.parse(signed_fname, format="trig")
    nanopuburl = dict(extracturl.namespaces())['this'].__str__()

    return nanopuburl

class FairWorkflow:
    def __init__(self, name='newworkflow'):
        self.np_uri = "http://purl.org/nanopub/temp/FAIRWorkflowsTest/workflow"
        self.THISWORKFLOW = rdflib.Namespace(self.np_uri + "/" + name + "/")
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
            rdf.add( (self.THISWORKFLOW[''], PWO.hasFirstStep, first_step.STEP['']) )

            # Add metadata from all the steps to this rdf graph
            for step in self.steps:
                rdf.add((step.STEP[''], PPLAN.isStepOfPlan, self.THISWORKFLOW['']))

                for var, arg in zip(step.func.__code__.co_varnames, step.args):
                    if isinstance(arg, FairStepEntry):
                        rdf.add((step.STEP[var], PPLAN.isOutputVarOf, arg.STEP['']))
                        rdf.add((arg.STEP[''], DUL.precedes, step.STEP['']))
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
        
    def nanopublish(self):
        # Publish all the steps individually
        for step in self.steps:
            step.nanopublish()

        # Publish the workflow itself
        nanopublish(assertionrdf=self.get_rdf(), uri=self.np_uri)


class FairStepEntry:
    def __init__(self, func, args, kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.executed = False
        self.result = None

        self.np_uri = "http://purl.org/nanopub/temp/FAIRWorkflowsTest/Step"
        self.THISSTEP = rdflib.Namespace(self.np_uri + '/' + func.__name__ + '/')

        self.STEP = self.THISSTEP

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
 
    def nanopublish(self):
        nanopuburl = nanopublish(assertionrdf=self.get_rdf(), uri=self.np_uri)
        self.STEP = rdflib.Namespace(nanopuburl + '/')

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
