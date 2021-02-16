import rdflib

from fairworkflows import namespaces
from fairworkflows.rdf_wrapper import RdfWrapper


class RetroProv(RdfWrapper):
    def __init__(self, prov_was_derived_from, log_message: str):
        super().__init__(uri=None, ref_name='retroprov')
        self.set_attribute(rdflib.RDF.type, namespaces.PROV.Activity)
        self.set_attribute(namespaces.PROV.wasDerivedFrom, rdflib.URIRef(prov_was_derived_from))
        self.rdf.add((self.self_ref, rdflib.RDFS.label, rdflib.Literal(log_message)))

    @property
    def prov_was_derived_from(self):
        """Refers to URI of object that this provenance was derived from.

        Matches the predicate prov:wasDerivedFrom associated to this retrospective provenance
        object
        """
        return self.get_attribute(namespaces.PROV.wasDerivedFrom)

    @prov_was_derived_from.setter
    def prov_was_derived_from(self, value):
        self.set_attribute(namespaces.PROV.wasDerivedFrom, rdflib.URIRef(value), overwrite=True)


class WorkflowRetroProv(RetroProv):
    def __init__(self, prov_was_derived_from, log_message):
        super().__init__(prov_was_derived_from, log_message)

    def __str__(self):
        """String representation."""
        s = f'Workflow retrospective provenance.\n'
        s += self._rdf.serialize(format='trig').decode('utf-8')
        return s


class StepRetroProv(RetroProv):
    def __init__(self, prov_was_derived_from, log_message):
        super().__init__(prov_was_derived_from, log_message)

    def __str__(self):
        """String representation."""
        s = f'Step retrospective provenance.\n'
        s += self._rdf.serialize(format='trig').decode('utf-8')
        return s
