import pyshacl
import rdflib

class FairStep:

    def __init__(self, step_rdf:rdflib.Graph = None, uri=None):
        
        if step_rdf:
            self.rdf = step_rdf
        else:
            self.rdf = rdflib.Graph()

    def validate(self):
        """
        Checks whether this step rdf has sufficient information required of
        a step in the Plex ontology.
        """
        shacl_graph = rdflib.Graph()

        r = pyshacl.validate(self.rdf, shacl_graph=shacl_graph)
        print(r)


#    def is_manual(self):
#        """
#        Returns true if this Plex step is a ManualTask
#        """
#        sub:step dcterms:description Literal 
#    a <http://dkm.fbk.eu/index.php/BPMN2_Ontology#ManualTask>, p-plan:Step        
