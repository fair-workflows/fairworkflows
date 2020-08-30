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

        self._steps = {}
        self._last_step_added = None

    def set_first_step(self, step:FairStep):
        self._rdf.add( (self.this_plan, Nanopub.PWO.hasFirstStep, rdflib.URIRef(step.uri)) )
        self._steps[step.uri] = step
        self._last_step_added = step
        print(self._steps)

    def add(self, new_step, follows=None):
        if not follows:
            if not self.first_step():
                self.set_first_step(new_step)
            else:
                self.add(new_step, follows=self._last_step_added)
        else:
            self._rdf.add( (rdflib.URIRef(follows.uri), Nanopub.DUL.precedes, rdflib.URIRef(new_step.uri)) )
            self._steps[new_step.uri] = new_step
            self._last_step_added = new_step

    def __iter__(self):
        return PlexIterator(self)

    def is_pplan_plan(self):
        if (self.this_plan, RDF.type, Nanopub.PPLAN.Plan) in self._rdf:
            return True
        else:
            return False

    def first_step(self):
        first_step = list(self._rdf.objects(subject=self.this_plan, predicate=Nanopub.PWO.hasFirstStep))
        if len(first_step) == 0:
            return None
        elif len(first_step) == 1:
            return first_step[0]
        else:
            return first_step

    def get_step(self, uri):
        return self._steps[uri]

    def description(self):
        descriptions = list(self._rdf.objects(subject=self.this_plan, predicate=DCTERMS.description))
        if len(descriptions) == 0:
            return None
        elif len(descriptions) == 1:
            return descriptions[0]
        else:
            return descriptions

    def validate(self, verbose=True):
        """
        Checks whether this workflow rdf has sufficient information required of
        a plan in the Plex ontology.
        """

        conforms = True
        log = ''

        if not self.is_pplan_plan():
            log += 'Plan RDF does not say it is a pplan:Plan\n'
            conforms = False

        if not self.description():
            log += 'Plan RDF has no dcterms:description\n'
            conforms = False

        if not self.first_step():
            log += 'Plan RDF does not specify a first step (pwo:hasFirstStep)\n'
            conforms = False
        elif len(self.first_step()) > 1:
            log += 'Plan RDF contains more than one first step (pwo:hasFirstStep)\n'
            conforms = False
            
        if verbose:
            print(log)

        return conforms


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
            
        nx.draw(G, pos=pos, with_labels=True, font_size=7, node_size=100, node_color='gray')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=7)
        plt.show()

    def __str__(self):
        s = f'Workflow URI = {self._uri}\n'
        s += self._rdf.serialize(format='trig').decode('utf-8')
        return s


class PlexIterator:

    def __init__(self, plex:FairWorkflow):
        self.plex = plex
        self.current_step = self.plex.first_step()
        self.deps = {}
        self.remaining = []
        for s, p, o in self.plex.rdf.triples((None, Nanopub.DUL.precedes, None)):
            if o not in self.deps:
                self.deps[o] = []
            self.deps[o].append(s)

            self.remaining.append(s)
            self.remaining.append(o)

        self.remaining = list(set(self.remaining))

#        print(self.deps)
#        print(self.remaining)

    def __next__(self):
        for step in self.remaining:
            can_run = True
            if step in self.deps:
                for dep in self.deps[step]:
                    if dep in self.remaining:
                        can_run = False
                        break
            if can_run == True:
                self.remaining.remove(step)
                return self.plex.get_step(str(step))

        raise StopIteration

