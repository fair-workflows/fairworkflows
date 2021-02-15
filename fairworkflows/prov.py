import rdflib

from fairworkflows import namespaces
from fairworkflows.rdf_wrapper import RdfWrapper


class RetroProv(RdfWrapper):
    def __init__(self, prov_was_derived_from, log_message: str):
        super().__init__(uri=None, ref_name='retroprov')
        self.rdf.add((self.self_ref, rdflib.RDF.type, namespaces.PROV.Activity))
        self.rdf.add((self.self_ref, namespaces.PROV.wasDerivedFrom,
                      rdflib.URIRef(prov_was_derived_from)))
        self.rdf.add((self.self_ref, rdflib.RDFS.label, rdflib.Literal(log_message)))


class WorkflowRetroProv(RetroProv):
    def __init__(self, prov_was_derived_from, log_message):
        super().__init__(prov_was_derived_from, log_message)
