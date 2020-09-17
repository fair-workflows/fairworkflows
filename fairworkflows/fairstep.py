import inspect
import time
import warnings
from typing import List
from urllib.parse import urldefrag

import rdflib
from rdflib import RDF, DCTERMS

from .nanopub import Nanopub
from .rdf_wrapper import RdfWrapper


class FairStep(RdfWrapper):
    """Represent a step in a fair workflow.

    Class for building, validating and publishing Fair Steps,
    as described by the plex ontology in the publication:
    Celebi, R., Moreira, J. R., Hassan, A. A., Ayyar, S., Ridder, L., Kuhn, T.,
    & Dumontier, M. (2019). Towards FAIR protocols and workflows: T
    he OpenPREDICT case study. arXiv preprint arXiv:1911.09531.

    Fair Steps may be fetched from Nanopublications, created from rdflib
    graphs or python functions.
    """

    DEFAULT_STEP_URI = 'http://purl.org/nanopub/temp/mynanopub#step'

    def __init__(self, uri=DEFAULT_STEP_URI):
        super().__init__(uri=uri)

    @classmethod
    def from_rdf(cls, rdf):
        """Construct Fair Step from existing RDF."""
        self = cls()
        self._rdf = rdf
        if self._uri not in rdf.subjects():
            warnings.warn(f"Warning: Provided URI '{self._uri}' does not "
                          f"match any subject in provided rdf graph.")
        return self

    @classmethod
    def from_nanopub(cls, uri):
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
        self = cls(uri=step_uri)

        # Check that the nanopub's assertion actually contains triples refering to the given step's uri
        if (rdflib.URIRef(self.self_ref), None, None) not in np.assertion:
            raise ValueError(f'No triples pertaining to the specified step (uri={step_uri}) were found in the assertion graph of the corresponding nanopublication (uri={np_uri})')

        # Else extract all triples in the assertion into the rdf graph for this step
        self._rdf += np.assertion

        return self

    @classmethod
    def from_function(cls, func):
        """
            Generates a plex rdf decription for the given python function, and makes this FairStep object a bpmn:ScriptTask.
        """
        name = func.__name__ + str(time.time())
        uri = 'http://purl.org/nanopub/temp/mynanopub#function' + name
        self = cls(uri=uri)
        code = inspect.getsource(func)

        # Set description of step to the raw function code
        self.description = code

        # Specify that step is a pplan:Step
        self.set_attribute(RDF.type, Nanopub.PPLAN.Step, overwrite=False)

        # Specify that step is a ScriptTask
        self.set_attribute(RDF.type, Nanopub.BPMN.ScriptTask, overwrite=False)

        return self

    @property
    def is_pplan_step(self):
        """Return True if this FairStep is a pplan:Step, else False."""
        return (self.self_ref, RDF.type, Nanopub.PPLAN.Step) in self._rdf

    @property
    def is_manual_task(self):
        """Returns True if this FairStep is a bpmn:ManualTask, else False."""
        return (self.self_ref, RDF.type, Nanopub.BPMN.ManualTask) in self._rdf

    @property
    def is_script_task(self):
        """Returns True if this FairStep is a bpmn:ScriptTask, else False."""
        return (self.self_ref, RDF.type, Nanopub.BPMN.ScriptTask) in self._rdf

    @property
    def inputs(self) -> List[rdflib.URIRef]:
        """Get inputs for this step."""
        return self.get_attribute(Nanopub.PPLAN.hasInputVar,
                                  always_return_list=True)

    @inputs.setter
    def inputs(self, uris: List[str]):
        """Set inputs for this step. Overwrite old inputs."""
        self.delete_attribute(Nanopub.PPLAN.hasInputVar)
        for uri in uris:
            self.set_attribute(Nanopub.PPLAN.hasInputVar, rdflib.URIRef(uri),
                               overwrite=False)

    @property
    def outputs(self) -> List[rdflib.URIRef]:
        """Get inputs for this step."""
        return self.get_attribute(Nanopub.PPLAN.hasOutputVar,
                                  always_return_list=True)

    @outputs.setter
    def outputs(self, uris: List[str]):
        """Set outputs for this step. Overwrite old inputs."""
        self.delete_attribute(Nanopub.PPLAN.hasOutputVar)
        for uri in uris:
            self.set_attribute(Nanopub.PPLAN.hasOutputVar, rdflib.URIRef(uri),
                               overwrite=False)

    @property
    def description(self):
        """Description.

        Returns the dcterms:description of this step (or a list, if more than
        one matching triple is found)
        """
        return self.get_attribute(DCTERMS.description)

    @description.setter
    def description(self, value):
        """
        Adds the given text string as a dcterms:description for this FairStep
        object.
        """
        self.set_attribute(DCTERMS.description, rdflib.term.Literal(value))

    def validate(self):
        """Validate step.

        Check whether this step rdf has sufficient information required of
        a step in the Plex ontology.
        """
        conforms = True
        log = ''

        if not self.is_pplan_step:
            log += 'Step RDF does not say it is a pplan:Step\n'
            conforms = False

        if not self.description:
            log += 'Step RDF has no dcterms:description\n'
            conforms = False

        if self.is_manual_task == self.is_script_task:
            log += 'Step RDF must be either a bpmn:ManualTask or a bpmn:ScriptTask\n'
            conforms = False

        assert conforms, log

    def __str__(self):
        """
            Returns string representation of this FairStep object.
        """
        s = f'Step URI = {self._uri}\n'
        s += self._rdf.serialize(format='trig').decode('utf-8')
        return s


