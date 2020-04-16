import os
import tempfile
from pathlib import Path
from config import NANOPUB_SCRIPT

import rdflib
from rdflib.namespace import RDF, RDFS, DC, XSD, OWL
import inspect
from datetime import datetime

# Some standard ontologies used for nanopubs and describing workflows.
NP = rdflib.Namespace("http://www.nanopub.org/nschema#")
PPLAN = rdflib.Namespace("http://purl.org/net/p-plan#")
PROV = rdflib.Namespace("http://www.w3.org/ns/prov#")
DUL = rdflib.Namespace("http://ontologydesignpatterns.org/wiki/Ontology:DOLCE+DnS_Ultralite/")
BPMN = rdflib.Namespace("https://www.omg.org/spec/BPMN/")
PWO = rdflib.Namespace("http://purl.org/spar/pwo/")


def publish_workflow(name, steps):
    fw = FairWorkflow(name)

    for step in steps:
        fw_step = FairStepEntry(step['code'], step['input'])
        fw.add_step(fw_step)

    fw.nanopublish()


class Nanopub:
    """
    Provides utility functions for creating and publishing RDF graphs as assertions in a nanopublication.
    """

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
        np_rdf.bind("prov", PROV)
        np_rdf.bind("dul", DUL)
        np_rdf.bind("bpmn", BPMN)
        np_rdf.bind("pwo", PWO)

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

        # Create a temporary dir for files created during serializing and signing
        tempdir = tempfile.mkdtemp()

        # Convert nanopub rdf to trig
        fname = 'temp.trig'
        unsigned_fname = os.path.join(tempdir, fname)
        signed_fname = os.path.join(tempdir, 'signed.' + fname)
        serialized = np_rdf.serialize(destination=unsigned_fname, format='trig')

        # Sign the nanopub and publish it
        os.system(f'{NANOPUB_SCRIPT} sign ' + unsigned_fname)
        os.system(f'{NANOPUB_SCRIPT} publish ' + signed_fname)

        # Extract nanopub URL
        # (this is pretty horrible, switch to python version as soon as it is ready)
        extracturl = rdflib.Graph()
        extracturl.parse(signed_fname, format="trig")
        nanopuburl = dict(extracturl.namespaces())['this'].__str__()

        print(f'Published to {nanopuburl}')
        return nanopuburl


class FairWorkflow:
    """
    Workflow is a list of FAIR Steps and their dependencies, which may optionally be executed.
    nanopublish() method allows this workflow and its constituent steps to be published as
    several individual nanopublications.
    """

    def __init__(self, name='newworkflow'):
        self.uri = "http://purl.org/nanopub/temp/FAIRWorkflowsTest/workflow"
        self.nanopub_uri = None  # None, until workflow is published

        # List of FAIR steps belonging to this workflow
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
        this_workflow = rdflib.Namespace(self.uri + "#")

        # Bind all non-standard prefixes in use
        rdf.bind("p-plan", PPLAN)
        rdf.bind("prov", PROV)
        rdf.bind("dul", DUL)
        rdf.bind("bpmn", BPMN)
        rdf.bind("pwo", PWO)

        # Add steps metadata
        if len(self.steps) > 0:

            # Workflow metadata
            first_step = self.steps[0]
            rdf.add( (this_workflow['workflow'], RDF.type, DUL.workflow) )
            rdf.add( (this_workflow['workflow'], PWO.hasFirstStep, first_step.ref()['step']) )

            # Add metadata from all the steps to this rdf graph
            for step in self.steps:
                rdf.add((step.ref()['step'], PPLAN.isStepOfPlan, this_workflow['workflow']))

                for var, arg in zip(step.func.__code__.co_varnames, step.args):
                    if isinstance(arg, FairStepEntry):
                        rdf.add((step.ref()[var], PPLAN.isOutputVarOf, arg.ref()['step']))
                        rdf.add((arg.ref()['step'], DUL.precedes, step.ref()['step']))
                    else:
                        binding = this_workflow[var + '_usage_' + str(arg)]
                        rdf.add((this_workflow[var], PROV.qualifiedUsage, binding))
                        rdf.add((binding, RDF.type, PROV.Usage))
                        rdf.add((binding, PROV.entity, this_workflow[var]))
                        rdf.add((binding, RDF.value, rdflib.Literal(f'{str(arg)}')))
        return rdf

    def ref(self):
        """
        Returns RDF Namespace that can be used externally to refer to this workflow.
        If the workflow has been nanopublished, this returns namespace of its nanopub
        URI instead.
        """
        if self.nanopub_uri is not None:
            return rdflib.Namespace(self.nanopub_uri + '#')
        else:
            return rdflib.Namespace(self.uri + '#')

    def __str__(self):
        return self.get_rdf().serialize(format='turtle').decode("utf-8")

    def rdf_to_file(self, fname, format='turtle'):
        return self.get_rdf().serialize(destination=fname, format=format)

    def nanopublish(self):
        """
        Publishes (as nanopublications) the workflow, as well as its constituent steps (all as separate nanopubs).

        """
        # Publish all the steps individually
        for step in self.steps:
            step.nanopublish()

        # Publish the workflow itself
        self.nanopub_uri = Nanopub.nanopublish(self.get_rdf(), uri=self.uri)


class FairStepEntry:
    """
    A python function, as a FAIR Step in a workflow. May be converted to RDF,
    and published as a nanopublication.
    """
    def __init__(self, code, kwargs):
        self.kwargs = kwargs
        self.executed = False
        self.result = None
        self.code = code

        self.uri = "http://purl.org/nanopub/temp/FAIRWorkflowsTest/Step"
        self.nanopub_uri = None  # None, until step is published

    def get_result(self):
        return self.result

    def ref(self):
        """
        Returns RDF Namespace that can be used externally to refer to this step.
        If the step has been nanopublished, this returns namespace of its nanopub
        URI instead.
        """
        if self.nanopub_uri is not None:
            return rdflib.Namespace(self.nanopub_uri + '#')
        else:
            return rdflib.Namespace(self.uri + '#')

    def get_rdf(self):
        """
        Autogenerate the rdf metadata for this step. Returns rdflib Graph.
        """

        rdf = rdflib.Graph()

        this_step = rdflib.Namespace(self.uri + '#')

        rdf.add((this_step['step'], RDF.type, PPLAN.Step))
        rdf.add((this_step['step'], RDF.type, BPMN.scriptTask))

        # TODO: Specify input values
        for kwarg in  self.kwargs:
            rdf.add((this_step[kwarg], RDF.type, PPLAN.Variable))

        # Grab entire function's source code for step 'description'
        func_src = Path(self.code).read_text()
        rdf.add((this_step['step'], DC.description, rdflib.Literal(func_src)))

        return rdf

    def nanopublish(self):
        """
        Publish this step's rdf as an assertion in a nanopublication.
        Stores the resulting publication URI, which will then be returned
        by future calls to this Step's ref() method.
        """
        self.nanopub_uri = Nanopub.nanopublish(self.get_rdf(), uri=self.uri)

    def __str__(self):
        """
        Serializes step rdf to string, for printing
        """
        return self.get_rdf().serialize(format='turtle').decode("utf-8")


def FairStep(fairworkflow):
    """
    Decorator to capture metadata about a function, and trace where its outputs are used.
    """
    def fair_wrapper(func):
        def metadata_wrapper(*args, **kwargs):

            # Add the new step to the workflow
            fairstep = FairStepEntry(func, args, kwargs)
            fairworkflow.add_step(fairstep)

            return fairstep
        return metadata_wrapper
    return fair_wrapper
