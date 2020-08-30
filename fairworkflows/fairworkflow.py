from .fairstep import FairStep
from .nanopub import Nanopub

import rdflib
from rdflib import RDF, DCTERMS

from rdflib.extras.external_graph_libs import rdflib_to_networkx_multidigraph
import matplotlib.pyplot as plt
import networkx as nx

class FairWorkflow:

    DEFAULT_PLAN_URI = 'http://purl.org/nanopub/temp/mynanopub#plan'

    def __init__(self, description, uri=DEFAULT_PLAN_URI):
        self._uri = uri
        self.this_plan = rdflib.URIRef(self._uri)

        self._rdf = rdflib.Graph()
        self._rdf.add( (self.this_plan, RDF.type, Nanopub.PPLAN.Plan) )
        self._rdf.add( (self.this_plan, DCTERMS.description, rdflib.term.Literal(description)) )

        self._last_step_added = None

    def set_first_step(self, step:FairStep):
        self._rdf.add( (self.this_plan, Nanopub.PWO.hasFirstStep, rdflib.URIRef(step.uri)) )
        self._last_step_added = step

    def add_step(self, new_step, parent_step):
        self._rdf.add( (rdflib.URIRef(parent_step.uri), Nanopub.DUL.precedes, rdflib.URIRef(new_step.uri)) )
        self._last_step_added = new_step

    def add_step_sequentially(self, new_step):
        if self._last_step_added is None:
            self.set_first_step(new_step)
        else:
            self.add_step(new_step, self._last_step_added)
            self._last_step_added = new_step


    @property
    def rdf(self):
        return self._rdf

    def draw(self):

        predicate_map = {}
        predicate_map[rdflib.term.URIRef('http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#precedes')] = 'precedes'
        predicate_map[rdflib.term.URIRef('http://purl.org/dc/terms/description')] = 'description'
        predicate_map[rdflib.term.URIRef('http://purl.org/spar/pwo#hasFirstStep')] = 'hasFirstStep'
        predicate_map[RDF.type] = 'a'

        G = nx.MultiDiGraph()
        edge_labels = {}
        for s, p, o in self._rdf:
            if p in predicate_map:
                edge_labels[(s,o)] = predicate_map[p]
                G.add_edge(s, o)

        pos = nx.spring_layout(G, scale=200, k = 1)
            
        nx.draw_networkx(G, pos=pos, with_labels=True, font_size=7, node_size=100, node_color='gray')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=7)
        plt.show()

    def __str__(self):
        s = f'Workflow URI = {self._uri}\n'
        s += self._rdf.serialize(format='trig').decode('utf-8')
        return s
