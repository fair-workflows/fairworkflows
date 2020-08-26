from .fairstep import FairStep
from .nanopub import Nanopub

import rdflib
from rdflib import RDF, DCTERMS

class FairWorkflow:

    DEFAULT_PLAN_URI = 'http://purl.org/nanopub/temp/mynanopub#plan'

    def __init__(self, description, uri=DEFAULT_PLAN_URI):
        self._uri = uri
        self.this_plan = rdflib.URIRef(self._uri)

        self._rdf = rdflib.Graph()
        self._rdf.add( (self.this_plan, RDF.type, Nanopub.PPLAN.Plan) )
        self._rdf.add( (self.this_plan, DCTERMS.description, rdflib.term.Literal(description)) )

    def set_first_step(self, step:FairStep):
        self._rdf.add( (self.this_plan, Nanopub.PWO.hasFirstStep, step.uri) )

    def add_step(self, new_step, precedes_step):
        print("What")
        self._rdf.add( (new_step.uri, Nanopub.DUL.precedes, precedes_step.uri) )
        print((new_step.uri, Nanopub.DUL.precedes, precedes_step.uri))

    @property
    def rdf(self):
        return self._rdf

    def __str__(self):
        s = f'Workflow URI = {self._uri}\n'
        s += self._rdf.serialize(format='trig').decode('utf-8')
        return s
