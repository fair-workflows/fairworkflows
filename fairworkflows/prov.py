import threading
from datetime import datetime
from typing import List, Iterator, Dict

import rdflib

from fairworkflows import namespaces
from fairworkflows.rdf_wrapper import RdfWrapper


class ProvLogger:
    """
    Simple logger for provenance. It allows storing items to a list in a thread-safe way.
    """
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


# prov_logger will be used as a singleton throughout the library to log provenance during execution
prov_logger = ProvLogger()


class StepRetroProv(RdfWrapper):
    """
    Represent retrospective provenance for a FAIR step execution.

    It holds the following information in its `rdf` attribute:
    * The uri of the prospective step that this retrospective provenance is associated with,
        as pplan:correspondsToStep predicate
    * Bindings of the input values to the prospective input variables of the associated step
    * Bindings of the output values to the prospective output variables of the associated step
    * The start and end time of step execution

    Attributes:
        step_uri: Refers to URI of step associated to this provenance.

    """
    def __init__(self, step=None, step_args: Dict = None, time_start: datetime = None,
                 time_end: datetime = None, output=None):
        """Constructor.

        Args:
            step: the associated FairStep object
            step_args: a dictionary containing the input arguments and values
            time_start: the start time of execution of the step
            time_end: the end time of execution of the step
        """
        super().__init__(uri=None, ref_name='fairstepprov')
        self.set_attribute(rdflib.RDF.type, namespaces.PPLAN.Activity)
        self.step = step
        self.step_uri = step.uri

        # Bind inputs
        for inputvar in step.inputs:
            if inputvar.name in step_args:
                self._add_retrospective_variable(inputvar, step_args[inputvar.name])

        # Bind outputs
        num_outputs = len(list(step.outputs))
        if num_outputs == 1:
            outvardict = {'out1': output}
        else:
            outvardict = {('out' + str(i)): outval for i, outval in enumerate(output) }

        for outputvar in step.outputs:
            if outputvar.name in outvardict:
                self._add_retrospective_variable(outputvar, outvardict[outputvar.name])

        # Add times to RDF (if available)
        if time_start:
            self.set_attribute(namespaces.PROV.startedAtTime, rdflib.Literal(time_start, datatype=rdflib.XSD.dateTime))
        if time_end:
            self.set_attribute(namespaces.PROV.endedAtTime, rdflib.Literal(time_end, datatype=rdflib.XSD.dateTime))

    def _add_retrospective_variable(self, prospective_var, value):
        """
        Add retrospective variable to rdf

        Args:
            prospective_var (FairVariable): FairVariable object of associated variable
            value: the variable value
        """
        retrovar = rdflib.BNode(prospective_var.name)
        self.set_attribute(namespaces.PROV.used, retrovar)
        self._rdf.add((retrovar, rdflib.RDF.type, namespaces.PPLAN.Entity))
        self._rdf.add((retrovar, rdflib.RDFS.label, rdflib.Literal(prospective_var.name)))
        self._rdf.add((retrovar, rdflib.RDF.value, rdflib.Literal(value)))

        if prospective_var.uri:
            self._rdf.add((retrovar, namespaces.PPLAN.correspondsToVariable, prospective_var.uri))

    @property
    def step_uri(self):
        """Refers to URI of step associated to this provenance.

        Matches the predicate pplan:correspondsToStep associated to this retrospective provenance
        """
        return self.get_attribute(namespaces.PPLAN.correspondsToStep)

    @step_uri.setter
    def step_uri(self, value):
        self.set_attribute(namespaces.PPLAN.correspondsToStep, rdflib.URIRef(value), overwrite=True)

    def publish_as_nanopub(self, use_test_server=False, **kwargs):
        """
        Publish this rdf as a nanopublication.

        Args:
            use_test_server (bool): Toggle using the test nanopub server.
            kwargs: Keyword arguments to be passed to [nanopub.Publication.from_assertion](
                https://nanopub.readthedocs.io/en/latest/reference/publication.html#
                nanopub.publication.Publication.from_assertion).
                This allows for more control over the nanopublication RDF.

        Returns:
            a dictionary with publication info, including 'nanopub_uri', and 'concept_uri'
        """
        return self._publish_as_nanopub(use_test_server=use_test_server, **kwargs)

    def __str__(self):
        """String representation."""
        s = f'Step retrospective provenance.\n'
        s += self._rdf.serialize(format='turtle').decode('utf-8')
        return s


class WorkflowRetroProv(RdfWrapper):
    """
    Represent the retrospective provenance of a FAIR workflow execution.

    It holds the following information in its 'rdf' attribute:
    * The uri of the prospective workflow that this retrospective provenance is associated with,
        as prov:wasDerivedFrom predicate
    * References to the retrospective provenance of the individual steps, indicated by the
        prov:hasMember predicate

    Attributes:
        workflow_uri: Refers to URI of workflow associated to this provenance.
    """
    def __init__(self, workflow, workflow_uri, step_provs: List[StepRetroProv]):
        """Constructor.

        Args:
            workflow: the FairWorkflow object corresponding to this retrospective prov
            workflow_uri: uri of the prospective workflow (NB: we do not use workflow.uri for
                this because the workflow can be unpublished.)
            step_provs: A list of StepRetroProv objects for each individual step of the workflow.

        """
        super().__init__(uri=None, ref_name='fairworkflowprov')
        self.set_attribute(rdflib.RDF.type, namespaces.PPLAN.Bundle)
        self.set_attribute(rdflib.RDF.type, namespaces.PROV.Collection)
        self.workflow = workflow
        self.workflow_uri = workflow_uri
        self._step_provs = step_provs

        # Add the Entity links for now (dummy links, if unpublished)
        for stepprov in self._step_provs:
            if stepprov.uri:
                self._rdf.add((self.self_ref, namespaces.PROV.hasMember, rdflib.URIRef(stepprov.uri)))
            else:
                self._rdf.add((self.self_ref, namespaces.PROV.hasMember, rdflib.URIRef('http://www.example.org/unpublished-entity-' + str(hash(stepprov)))))

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

    def publish_as_nanopub(self, use_test_server=False, **kwargs):
        """
        Publish this rdf as a nanopublication.

        Args:
            use_test_server (bool): Toggle using the test nanopub server.
            kwargs: Keyword arguments to be passed to [nanopub.Publication.from_assertion](
                https://nanopub.readthedocs.io/en/latest/reference/publication.html#
                nanopub.publication.Publication.from_assertion).
                This allows for more control over the nanopublication RDF.

        Returns:
            a dictionary with publication info, including 'nanopub_uri', and 'concept_uri'
        """

        # Clear existing members of this entity (to be replaced with newly published links)
        self.remove_attribute(namespaces.PROV.hasMember)

        for stepprov in self._step_provs:
            stepprov.publish_as_nanopub(use_test_server=use_test_server, **kwargs)
            self._rdf.add((self.self_ref, namespaces.PROV.hasMember, rdflib.URIRef(stepprov.uri)))

        return self._publish_as_nanopub(use_test_server=use_test_server, **kwargs)

    def __str__(self):
        """String representation."""
        s = f'Workflow retrospective provenance.\n'
        s += self._rdf.serialize(format='turtle').decode('utf-8')
        return s
