from .nanopub import Nanopub
import pyshacl
import rdflib
from rdflib import RDF, DCTERMS

class FairStep:

    DEFAULT_STEP_URI = 'http://purl.org/nanopub/temp/mynanopub#step'

    def __init__(self, step_rdf:rdflib.Graph = None, uri = DEFAULT_STEP_URI):

        self._uri = uri

        if step_rdf:
            self._rdf = step_rdf

            if self._uri not in step_rdf.subjects():
                print(f"Warning: Provided URI '{self._uri}' does not match any subject in provided rdf graph.")
        else:
            self._rdf = rdflib.Graph()

        self.this_step = rdflib.URIRef(self._uri)

    @property
    def rdf(self):
        return self._rdf

    @property
    def uri(self):
        return self._uri

    def is_pplan_step(self):
        if (self.this_step, RDF.type, Nanopub.PPLAN.Step) in self._rdf:
            return True
        else:
            return False

    def is_manual_task(self):
        if (self.this_step, RDF.type, Nanopub.BPMN.ManualTask) in self._rdf:
            return True
        else:
            return False

    def is_script_task(self):
        if (self.this_step, RDF.type, Nanopub.BPMN.ScriptTask) in self._rdf:
            return True
        else:
            return False
        
    def description(self):
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
        a step in the Plex ontology.
        """

        conforms = True
        log = ''

        if not self.is_pplan_step():
            log += 'Step RDF does not say it is a pplan:step\n'
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
        s = f'Step URI = {self._uri}\n'
        s += self._rdf.serialize(format='trig').decode('utf-8')
        return s
