import inspect
import time
import warnings
from copy import deepcopy
from typing import List

import rdflib
from rdflib import RDF, RDFS, DCTERMS


from fairworkflows import namespaces
from fairworkflows.rdf_wrapper import RdfWrapper

FAIRSTEP_PREDICATES = [RDF.type, namespaces.PPLAN.hasInputVar,
                       namespaces.PPLAN.hasOutputVar, DCTERMS.description, RDFS.label]


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

    def __init__(self, uri=None):
        super().__init__(uri=uri, ref_name='step')

    @classmethod
    def from_rdf(cls, rdf, uri, fetch_references: bool = False, force: bool = False):
        """Construct Fair Step from existing RDF.

        Args:
            rdf: The RDF graph
            uri: Uri of the object
            fetch_references: Boolean toggling whether to fetch objects from nanopub that are
                referred by this object. For a FairStep there are currently no references supported.
            force: Toggle forcing creation of object even if url is not in any of the subjects of
                the passed RDF
        """
        cls._uri_is_subject_in_rdf(uri, rdf, force=force)
        self = cls(uri)
        self._rdf = deepcopy(rdf)  # Make sure we don't mutate user RDF
        self.anonymise_rdf()
        self.remove_non_attribute_triples()
        return self

    @classmethod
    def from_function(cls, function):
        """
            Generates a plex rdf decription for the given python function, and makes this FairStep object a bpmn:ScriptTask.
        """
        name = function.__name__ + str(time.time())
        uri = 'http://purl.org/nanopub/temp/mynanopub#function' + name
        self = cls(uri=uri)
        code = inspect.getsource(function)

        # Set description of step to the raw function code
        self.description = code

        # Set a label for this step
        self.label = function.__name__

        # Specify that step is a pplan:Step
        self.set_attribute(RDF.type, namespaces.PPLAN.Step, overwrite=False)

        # Specify that step is a ScriptTask
        self.set_attribute(RDF.type, namespaces.BPMN.ScriptTask, overwrite=False)

        return self

    @property
    def is_pplan_step(self):
        """Return True if this FairStep is a pplan:Step, else False."""
        return (self.self_ref, RDF.type, namespaces.PPLAN.Step) in self._rdf

    @property
    def is_manual_task(self):
        """Returns True if this FairStep is a bpmn:ManualTask, else False."""
        return (self.self_ref, RDF.type, namespaces.BPMN.ManualTask) in self._rdf

    @property
    def is_script_task(self):
        """Returns True if this FairStep is a bpmn:ScriptTask, else False."""
        return (self.self_ref, RDF.type, namespaces.BPMN.ScriptTask) in self._rdf

    @property
    def inputs(self) -> List[rdflib.URIRef]:
        """Inputs for this step.

        Inputs are a list of URIRef's. The URIs should point to
        a pplan.Variable, for example: www.purl.org/stepuri#inputvarname.
        Set inputs by passing a list of strings depicting URIs. This
        overwrites old inputs.
        """
        return self.get_attribute(namespaces.PPLAN.hasInputVar,
                                  return_list=True)

    @inputs.setter
    def inputs(self, uris: List[str]):
        self.remove_attribute(namespaces.PPLAN.hasInputVar)
        for uri in uris:
            self.set_attribute(namespaces.PPLAN.hasInputVar, rdflib.URIRef(uri),
                               overwrite=False)

    @property
    def outputs(self) -> List[rdflib.URIRef]:
        """Get inputs for this step.

        Outputs are a list of URIRef's. The URIs should point to
        a pplan.Variable, for example: www.purl.org/stepuri#outputvarname.
        Set outputs by passing a list of strings depicting URIs. This
        overwrites old outputs.
        """
        return self.get_attribute(namespaces.PPLAN.hasOutputVar,
                                  return_list=True)

    @outputs.setter
    def outputs(self, uris: List[str]):
        self.remove_attribute(namespaces.PPLAN.hasOutputVar)
        for uri in uris:
            self.set_attribute(namespaces.PPLAN.hasOutputVar, rdflib.URIRef(uri),
                               overwrite=False)

    @property
    def label(self):
        """Label.

        Returns the rdfs:label of this step (or a list, if more than one matching triple is found)
        """
        return self.get_attribute(RDFS.label)

    @label.setter
    def label(self, value):
        """
        Adds the given text string as an rdfs:label for this FairStep
        object.
        """
        self.set_attribute(RDFS.label, rdflib.term.Literal(value))

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

        if not self.label:
            log += 'Step RDF has no rdfs:label\n'
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
