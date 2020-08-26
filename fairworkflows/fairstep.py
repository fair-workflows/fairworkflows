from .nanopub import Nanopub
import pyshacl
import rdflib
from rdflib import RDF, DCTERMS

class FairStep:

    DEFAULT_STEP_URI = 'http://purl.org/nanopub/temp/mynanopub#step'

    def __init__(self, step_rdf:rdflib.Graph = None, uri=None):
        
        if step_rdf:
            self.rdf = step_rdf
        else:
            self.rdf = rdflib.Graph()

        if uri:
            self.uri = uri
        else:
            self.uri = self.DEFAULT_STEP_URI

        self.this_step = rdflib.URIRef(self.uri)

    def is_pplan_step(self):
        if (self.this_step, RDF.type, Nanopub.PPLAN.Step) in self.rdf:
            return True
        else:
            return False

    def is_manual_task(self):
        if (self.this_step, RDF.type, Nanopub.BPMN.ManualTask) in self.rdf:
            return True
        else:
            return False

    def is_script_task(self):
        if (self.this_step, RDF.type, Nanopub.BPMN.ScriptTask) in self.rdf:
            return True
        else:
            return False
        
    def description(self):
        descriptions = list(self.rdf.objects(subject=self.this_step, predicate=DCTERMS.description))
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
