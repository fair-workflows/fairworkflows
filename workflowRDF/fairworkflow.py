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


class Nanopub:

    @staticmethod
    def rdf(assertionrdf, uri='http://purl.org/nanopub/temp/mynanopub'):
        """
        Return the nanopub rdf, with given assertion and URI, but does not sign or publish.
        """

        this_np = rdflib.Namespace(uri+'#')

        # Set up different contexts
        np_rdf = rdflib.ConjunctiveGraph()
        head = rdflib.Graph(np_rdf.store, this_np.Head)
        assertion = rdflib.Graph(np_rdf.store, this_np.assertion)
        provenance = rdflib.Graph(np_rdf.store, this_np.provenance)
        pubInfo = rdflib.Graph(np_rdf.store, this_np.pubInfo)

        np_rdf.bind("", this_np)
        np_rdf.bind("np", NP)

        np_rdf.bind("p-plan", PPLAN)
        np_rdf.bind("edam", EDAM)
        np_rdf.bind("prov", PROV)
        np_rdf.bind("dul", DUL)
        np_rdf.bind("bpmn", BPMN)
        np_rdf.bind("pwo", PWO)
        np_rdf.bind("rdfg", RDFG)

        head.add((this_np[''], RDF.type, NP.Nanopublication))
        head.add((this_np[''], NP.hasAssertion, this_np.assertion))
        head.add((this_np[''], NP.hasProvenance, this_np.provenance))
        head.add((this_np[''], NP.hasPublicationInfo, this_np.pubInfo))

        assertion += assertionrdf

        creationtime = rdflib.Literal(datetime.now(),datatype=XSD.dateTime)
        provenance.add((this_np.assertion, PROV.generatedAtTime, creationtime))
        provenance.add((this_np.assertion, PROV.wasDerivedFrom, this_np.experiment)) 
        provenance.add((this_np.assertion, PROV.wasAttributedTo, this_np.experimentScientist))

        pubInfo.add((this_np[''], PROV.wasAttributedTo, this_np.DrBob))
        pubInfo.add((this_np[''], PROV.generatedAtTime, creationtime))

        return np_rdf


    @staticmethod
    def nanopublish(assertionrdf, uri=None):
        """
        Publish the given assertion as a nanopublication with the given URI.
        Uses np commandline tool to sign and publish.
        """

        np_rdf = Nanopub.rdf(assertionrdf, uri=uri)

        # Convert nanopub rdf to trig
        fname = 'temp.trig'
        serialized = np_rdf.serialize(destination=fname, format='trig')

        # Sign the nanopub and publish it
        os.system('np sign ' + fname)
        signed_fname = 'signed.' + fname
        os.system('np publish ' + signed_fname)

        # Extract nanopub URL
        # (this is pretty horrible, switch to python version as soon as it is ready)
        extracturl = rdflib.Graph()
        extracturl.parse(signed_fname, format="trig")
        nanopuburl = dict(extracturl.namespaces())['this'].__str__()

        return nanopuburl


class FairWorkflow:
    def __init__(self, name='newworkflow'):
        self.np_uri = "http://purl.org/nanopub/temp/FAIRWorkflowsTest/workflow"
        self.this_workflow = rdflib.Namespace(self.np_uri + "#")
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
            rdf.add( (self.this_workflow['workflow'], RDF.type, DUL.workflow) )
            rdf.add( (self.this_workflow['workflow'], PWO.hasFirstStep, first_step.STEP['step']) )

            # Add metadata from all the steps to this rdf graph
            for step in self.steps:
                rdf.add((step.STEP['step'], PPLAN.isStepOfPlan, self.this_workflow['workflow']))

                for var, arg in zip(step.func.__code__.co_varnames, step.args):
                    if isinstance(arg, FairStepEntry):
                        rdf.add((step.STEP[var], PPLAN.isOutputVarOf, arg.STEP['step']))
                        rdf.add((arg.STEP['step'], DUL.precedes, step.STEP['step']))
                    else:
                        binding = self.this_workflow[var + '_usage_' + str(arg)]
                        rdf.add((self.this_workflow[var], PROV.qualifiedUsage, binding))
                        rdf.add((binding, RDF.type, PROV.Usage))
                        rdf.add((binding, PROV.entity, self.this_workflow[var]))
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
        Nanopub.nanopublish(self.get_rdf(), uri=self.np_uri)


class FairStepEntry:
    def __init__(self, func, args, kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.executed = False
        self.result = None

        self.np_uri = "http://purl.org/nanopub/temp/FAIRWorkflowsTest/Step"
        self.THISSTEP = rdflib.Namespace(self.np_uri + '#')
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

        rdf.add((self.THISSTEP['step'], RDF.type, PPLAN.Step))
        rdf.add((self.THISSTEP['step'], RDF.type, BPMN.scriptTask))

        for var, arg in zip(self.func.__code__.co_varnames, self.args):
            rdf.add((self.THISSTEP[var], RDF.type, PPLAN.Variable))
            rdf.add((self.THISSTEP['step'], PPLAN.hasInputVar, self.THISSTEP[var]))

        # Grab entire function's source code for step 'description'
        func_src = inspect.getsource(self.func)
        rdf.add((self.THISSTEP['step'], DC.description, rdflib.Literal(func_src)))

        return rdf
 
    def nanopublish(self):
        nanopuburl = Nanopub.nanopublish(self.get_rdf(), uri=self.np_uri)
        self.STEP = rdflib.Namespace(nanopuburl + '#')

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
