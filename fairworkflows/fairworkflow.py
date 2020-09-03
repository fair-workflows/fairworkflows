from .fairstep import FairStep
from .nanopub import Nanopub

import rdflib
from rdflib import RDF, DCTERMS

from rdflib.extras.external_graph_libs import rdflib_to_networkx_multidigraph
import matplotlib.pyplot as plt
import networkx as nx

DEFAULT_PLAN_URI = 'http://purl.org/nanopub/temp/mynanopub#plan'


class FairWorkflow:

    """
        Class for building, validating and publishing Fair Workflows, as described by the plex ontology in the publication:

        Celebi, R., Moreira, J. R., Hassan, A. A., Ayyar, S., Ridder, L., Kuhn, T., & Dumontier, M. (2019). Towards FAIR protocols and workflows: The OpenPREDICT case study. arXiv preprint arXiv:1911.09531.

        Fair Workflows may be fetched from Nanopublications, or created through the addition of FairStep's.
    """

    def __init__(self, description, uri=DEFAULT_PLAN_URI):
        self._uri = uri
        self.this_plan = rdflib.URIRef(self._uri)

        self._rdf = rdflib.Graph()
        self._rdf.add( (self.this_plan, RDF.type, Nanopub.PPLAN.Plan) )
        self._rdf.add( (self.this_plan, DCTERMS.description, rdflib.term.Literal(description)) )

        self._steps = {}
        self._last_step_added = None

    def set_first_step(self, step:FairStep):
        """
            Sets the first step of this plex workflow to the given FairStep
        """
        self._rdf.add( (self.this_plan, Nanopub.PWO.hasFirstStep, rdflib.URIRef(step.uri)) )
        self._steps[step.uri] = step
        self._last_step_added = step

    def add(self, step:FairStep, follows:FairStep=None):
        """
            Adds the specified FairStep to the workflow rdf. If 'follows' is specified,
            then it dul:precedes the step. If 'follows' is None, the last added step (to this workflow)
            dul:precedes the step. If no steps have yet been added to the workflow, and 'follows' is None,
            then this step is automatically set to by the first step in the workflow.
        """
        if not follows:
            if not self.first_step():
                self.set_first_step(step)
            else:
                self.add(step, follows=self._last_step_added)
        else:
            self._rdf.add( (rdflib.URIRef(follows.uri), Nanopub.DUL.precedes, rdflib.URIRef(step.uri)) )
            self._steps[step.uri] = step
            self._last_step_added = step

    def __iter__(self):
        """
        Iterate over this FairWorkflow, return one step at a
        time in the order specified by the precedes relations (
        i.e. topologically sorted).
        """
        G = nx.MultiDiGraph()
        for s, p, o in self._rdf:
            if p == Nanopub.DUL.precedes:
                G.add_edge(s, o)
        for step_uri in nx.topological_sort(G):
            yield self.get_step(str(step_uri))

    def is_pplan_plan(self):
        """
            Returns True if this object's rdf specifies that it is a pplan:Plan
        """
        if (self.this_plan, RDF.type, Nanopub.PPLAN.Plan) in self._rdf:
            return True
        else:
            return False

    def first_step(self):
        """
            Returns the first step in this plex workflow, if currently specified, otherwise None.
            If more than one first step is specified in the rdf (this is bad) then the list of
            'first' steps is returned.
        """
        first_step = list(self._rdf.objects(subject=self.this_plan, predicate=Nanopub.PWO.hasFirstStep))

        if len(first_step) == 0:
            return None
        elif len(first_step) == 1:
            return first_step[0]
        else:
            return first_step

    def get_step(self, uri):
        """
            Returns the FairStep instance associated with the given step URI (if such a step was added to this workflow)
        """
        return self._steps[uri]

    def description(self):
        """
            Returns any dcterms:description found in the rdf for this workflow (returns a list if more than one matching triple found)
        """
        descriptions = list(self._rdf.objects(subject=self.this_plan, predicate=DCTERMS.description))
        if len(descriptions) == 0:
            return None
        elif len(descriptions) == 1:
            return descriptions[0]
        else:
            return descriptions

    def validate(self, verbose=True):
        """
            Checks whether this workflow's rdf has sufficient information required of
            a workflow in the Plex ontology. If not, a message is printed explaining
            the problem, and the function returns False.

            If verbose is set to False, no explanation messages will be printed.
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
        elif len(self.first_step()) > 1 and isinstance(self.first_step(), list):
            log += f'Plan RDF contains more than one first step (pwo:hasFirstStep): {self.first_step()}\n'
            conforms = False

        if verbose:
            print(log)

        return conforms


    @property
    def rdf(self):
        """
            Getter for the rdf graph describing this FairWorkflow.
        """
        return self._rdf

    def draw(self, show=True):
        """
            Ugly networkx implementation of graph visualization for this plex workflow.
            If show is False, the plot will not be displayed to screen.
        """

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

        if show is True:
            plt.show()

    def __str__(self):
        """
            Returns string representation of this FairWorkflow object.
        """
        s = f'Workflow URI = {self._uri}\n'
        s += self._rdf.serialize(format='trig').decode('utf-8')
        return s
