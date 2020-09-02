from .nanopub import Nanopub
import rdflib
from rdflib import RDF, DCTERMS
from urllib.parse import urldefrag
import inspect

class FairStep:
    """
        Class for building, validating and publishing Fair Steps, as described by the plex ontology in the publication:

        Celebi, R., Moreira, J. R., Hassan, A. A., Ayyar, S., Ridder, L., Kuhn, T., & Dumontier, M. (2019). Towards FAIR protocols and workflows: The OpenPREDICT case study. arXiv preprint arXiv:1911.09531.

        Fair Steps may be fetched from Nanopublications, or created from rdflib graphs or python functions.
    """


    DEFAULT_STEP_URI = 'http://purl.org/nanopub/temp/mynanopub#step'

    def __init__(self, step_rdf:rdflib.Graph = None, uri = DEFAULT_STEP_URI, from_nanopub=False, func=None):

        if func:
            self.from_function(func)
        elif from_nanopub:
            self.load_from_nanopub(uri)
        else:
            self._uri = uri

            if step_rdf:
                self._rdf = step_rdf

                if self._uri not in step_rdf.subjects():
                    print(f"Warning: Provided URI '{self._uri}' does not match any subject in provided rdf graph.")
            else:
                self._rdf = rdflib.Graph()

        self.this_step = rdflib.URIRef(self._uri)


    def load_from_nanopub(self, uri):
        """
            Fetches the nanopublication corresponding to the specified URI, and attempts to extract the rdf describing a fairstep from
            its assertion graph. If the URI passed to this function is the uri of the nanopublication (and not the step itself) then
            an attempt will be made to identify what the URI of the step actually is, by checking if the nanopub npx:introduces a
            particular concept.

            If the assertion graph does not contain any triples with the step URI as subject, an exception is raised. If such triples
            are found, then ALL triples in the assertion are added to the rdf graph for this FairStep.
        """


        # Work out the nanopub URI by defragging the step URI
        np_uri, frag = urldefrag(uri)

        # Fetch the nanopub
        np = Nanopub.fetch(np_uri)

        # If there was no fragment in the original uri, then the uri was already the nanopub one.
        # Try to work out what the step's URI is, by looking at what the np is introducing.
        if len(frag) == 0:
            concepts_introduced = []
            for s, p, o in np.pubinfo.triples((None, Nanopub.NPX.introduces, None)):
                concepts_introduced.append(o)

            if len(concepts_introduced) == 0:
                raise ValueError('This nanopub does not introduce any concepts. Please provide URI to the step itself (not just the nanopub).')
            elif len(concepts_introduced) > 0:
                step_uri = concepts_introduced[0]

            print('Assuming step URI is', step_uri)

        else:
            step_uri = uri

        self._uri = step_uri
        self.this_step = rdflib.URIRef(self._uri)

        # Check that the nanopub's assertion actually contains triples refering to the given step's uri 
        if (rdflib.URIRef(self.this_step), None, None) not in np.assertion:
            raise ValueError(f'No triples pertaining to the specified step (uri={step_uri}) were found in the assertion graph of the corresponding nanopublication (uri={np_uri})')

        # Else extract all triples in the assertion into the rdf graph for this step
        self._rdf = rdflib.Graph()
        self._rdf += np.assertion


    def from_function(self, func):
        """
            Generates a plex rdf decription for the given python function, and makes this FairStep object a bpmn:ScriptTask.
        """
        import time
        name = func.__name__ + str(time.time())
        self._rdf = rdflib.Graph()
        code = inspect.getsource(func)
        self._uri = 'http://purl.org/nanopub/temp/mynanopub#function' + name
        self.this_step = rdflib.URIRef(self._uri)

        # Set description of step to the raw function code
        self.add_description(code)

        # Specify that step is a pplan:Step
        self._rdf.add( (self.this_step, RDF.type, Nanopub.PPLAN.Step) )

        # Specify that step is a ScriptTask
        self._rdf.add( (self.this_step, RDF.type, Nanopub.BPMN.ScriptTask) )


    def add_description(self, text):
        """
            Adds the given text string as a dcterms:description for this FairStep object.
        """
        self._rdf.add( (self.this_step, DCTERMS.description, rdflib.term.Literal(text)) )


    @property
    def rdf(self):
        """
            Getter for the rdf graph describing this FairStep.
        """
        return self._rdf

    @property
    def uri(self):
        """
            Getter for the URI of this FairStep.
        """
        return self._uri

    def is_pplan_step(self):
       """
            Returns True if this FairStep is a pplan:Step, else False.
       """
       if (self.this_step, RDF.type, Nanopub.PPLAN.Step) in self._rdf:
            return True
        else:
            return False

    def is_manual_task(self):
        """
            Returns True if this FairStep is a bpmn:ManualTask, else False.
       """
       if (self.this_step, RDF.type, Nanopub.BPMN.ManualTask) in self._rdf:
            return True
        else:
            return False

    def is_script_task(self):
       """
            Returns True if this FairStep is a bpmn:ScriptTask, else False.
       """
        if (self.this_step, RDF.type, Nanopub.BPMN.ScriptTask) in self._rdf:
            return True
        else:
            return False
        

    def description(self):
       """
            Returns the dcterms:description of this step (or a list, if more than one matching triple is found)
       """

        descriptions = list(self._rdf.objects(subject=self.this_step, predicate=DCTERMS.description))
        if len(descriptions) == 0:
            return None
        elif len(descriptions) == 1:
            return descriptions[0]
        else:
            return descriptions

            
    def validate(self, verbose=True):
        """
            Checks whether this step rdf has sufficient information required of
            a step in the Plex ontology. If not, a message is printed explaining
            the problem, and the function returns False.

            If verbose is set to False, no explanation messages will be printed.
        """

        conforms = True
        log = ''

        if not self.is_pplan_step():
            log += 'Step RDF does not say it is a pplan:Step\n'
            conforms = False

        if not self.description():
            log += 'Step RDF has no dcterms:description\n'
            conforms = False

        if self.is_manual_task() == self.is_script_task():
            log += 'Step RDF must be either a bpmn:ManualTask or a bpmn:ScriptTask\n'
            conforms = False

        if verbose:
            print(log)

        return conforms


    def __str__(self):
        """
            Returns string representation of this FairStep object.
        """
        s = f'Step URI = {self._uri}\n'
        s += self._rdf.serialize(format='trig').decode('utf-8')
        return s
