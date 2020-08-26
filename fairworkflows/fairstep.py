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
        

    def validate(self):
        """
        Checks whether this step rdf has sufficient information required of
        a step in the Plex ontology.
        """

        # Use shacl later (once the schema is properly defined)
        #
        #shacl_graph = rdflib.Graph()
        #ex = rdflib.Namespace('http://www.example.com/ns#')
        #shacl_graph.add( (ex.PlexStepShape, RDF.type, Nanopub.PPLAN.Plan) )
        #conforms, results_graph, results_txt = pyshacl.validate(self.rdf, shacl_graph=shacl_graph)
        #print(results_txt)
        #return conforms

        conforms = True

        necessary_triples = [
            (self.this_step, RDF.type, Nanopub.PPLAN.Step), # Must be a pplan:Step
            (self.this_step, DCTERMS.description, None)     # Must have a dcterms:description
        ]
        for t in necessary_triples:
            if t not in self.rdf:
                print("Plex step is missing triple of the form:", t)
                conforms = False

        return conforms


#    def is_manual(self):
#        """
#        Returns true if this Plex step is a ManualTask
#        """
#        sub:step dcterms:description Literal 
#    a <http://dkm.fbk.eu/index.php/BPMN2_Ontology#ManualTask>, p-plan:Step        
