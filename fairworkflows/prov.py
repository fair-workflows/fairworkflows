import threading
from datetime import datetime
from typing import List, Iterator

import rdflib

from fairworkflows import namespaces
from fairworkflows.rdf_wrapper import RdfWrapper


class ProvLogger:
    def __init__(self):
        self.lock = threading.Lock()
        self.items = []

    def add(self, item):
        with self.lock:
            self.items.append(item)

    def get_all(self):
        with self.lock:
            items, self.items = self.items, []
        return items

    def empty(self):
        self.items = []


prov_logger = ProvLogger()


class RetroProv(RdfWrapper):
    def __init__(self):
        super().__init__(uri=None, ref_name='retroprov')
        self.timestamp = datetime.now()


class StepRetroProv(RetroProv):
    def __init__(self, step=None, step_args=None, time_start:datetime = None, time_end:datetime = None):
        super().__init__()
        self.set_attribute(rdflib.RDF.type, namespaces.PPLAN.Activity)
        self.step = step
        self.step_uri = step.uri

        stepbase = rdflib.Namespace(step.uri)

        # Bind inputs
        for inputvar in step.inputs:
            if inputvar.name in step_args:
                self._rdf.add( (inputvar.uri, rdflib.RDF.value, rdflib.Literal(step_args[inputvar.name])) )

        # Add times to RDF (if available)
        if time_start:
            self.set_attribute(namespaces.PROV.startedAtTime, rdflib.Literal(time_start, datatype=rdflib.XSD.dateTime))
        if time_end:
            self.set_attribute(namespaces.PROV.endedAtTime, rdflib.Literal(time_end, datatype=rdflib.XSD.dateTime))

    @property
    def step_uri(self):
        """Refers to URI of step associated to this provenance.

        Matches the predicate pplan:correspondsToStep associated to this retrospective provenance
        """
        return self.get_attribute(namespaces.PPLAN.correspondsToStep)

    @step_uri.setter
    def step_uri(self, value):
        self.set_attribute(namespaces.PPLAN.correspondsToStep, rdflib.URIRef(value), overwrite=True)

    def __str__(self):
        """String representation."""
        s = f'Step retrospective provenance.\n'
        s += self._rdf.serialize(format='trig').decode('utf-8')
        return s


class WorkflowRetroProv(RetroProv):
    def __init__(self, workflow, workflow_uri, step_provs: List[StepRetroProv]):
        super().__init__()
        self.set_attribute(rdflib.RDF.type, namespaces.PPLAN.Bundle)
        self.workflow = workflow
        self.workflow_uri = workflow_uri
        self._step_provs = step_provs

    @property
    def workflow_uri(self):
        """Refers to URI of step associated to this provenance.

        Matches the predicate prov:wasDerivedFrom associated to this retrospective provenance
        """
        return self.get_attribute(namespaces.PROV.wasDerivedFrom)

    @workflow_uri.setter
    def workflow_uri(self, value):
        self.set_attribute(namespaces.PROV.wasDerivedFrom, rdflib.URIRef(value), overwrite=True)

    def __iter__(self) -> Iterator[StepRetroProv]:
        """Iterate over StepRetroProv that were part of the execution of the workflow."""
        yield from self._step_provs

    def __len__(self) -> int:
        return len(self._step_provs)

    def __str__(self):
        """String representation."""
        s = f'Workflow retrospective provenance.\n'
        s += self._rdf.serialize(format='trig').decode('utf-8')
        return s
