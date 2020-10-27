import warnings
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator, Tuple, List, Optional

import networkx as nx
import rdflib
from rdflib import RDF, DCTERMS
from rdflib.tools.rdf2dot import rdf2dot
from requests import HTTPError

from fairworkflows import namespaces
from fairworkflows.fairstep import FairStep, FAIRSTEP_PREDICATES
from fairworkflows.rdf_wrapper import RdfWrapper


class FairWorkflow(RdfWrapper):

    """
        Class for building, validating and publishing Fair Workflows, as described by the plex ontology in the publication:

        Celebi, R., Moreira, J. R., Hassan, A. A., Ayyar, S., Ridder, L., Kuhn, T., & Dumontier, M. (2019). Towards FAIR protocols and workflows: The OpenPREDICT case study. arXiv preprint arXiv:1911.09531.

        Fair Workflows may be fetched from Nanopublications, or created through the addition of FairStep's.
    """

    def __init__(self, description=None, label=None, uri=None):
        super().__init__(uri=uri, ref_name='plan')

        self._is_published = False

        self._rdf.add((self.self_ref, RDF.type, namespaces.PPLAN.Plan))
        self.description = description
        self.label = label
        self._steps = {}
        self._last_step_added = None

    @classmethod
    def from_rdf(cls, rdf: rdflib.Graph, uri: str = None,
                 fetch_steps: bool = False):
        """Construct Fair Workflow from existing RDF.

        Args:
            rdf: RDF graph containing information about the workflow and
                possibly it's associated steps. Should use plex ontology.
            uri: URI of the workflow
            fetch_steps: toggles fetching steps. I.e. if we encounter steps
                that are part of the workflow, but are not specified in the
                RDF we try fetching them from nanopub
        """
        rdf = deepcopy(rdf)  # Make sure we don't mutate user RDF
        if rdflib.URIRef(uri) not in rdf.subjects():
            warnings.warn(f"Warning: Provided URI '{uri}' does not "
                          f"match any subject in provided rdf graph.")
        self = cls(uri=uri)
        self._extract_steps(rdf, uri, fetch_steps)
        self._rdf = rdf
        self.anonymise_rdf()
        return self

    def _extract_steps(self, rdf, uri, fetch_steps=False):
        """Extract FairStep objects from rdf.

        Create FairStep objects for all steps in the passed RDF. Removes
        triples describing steps from rdf, those will be represented in
        the separate step RDF. Optionally try to fetch steps from nanopub.
        """
        step_refs = rdf.subjects(predicate=namespaces.PPLAN.isStepOfPlan,
                                 object=rdflib.URIRef(uri))
        for step_ref in step_refs:
            step_uri = str(step_ref)
            step = self._extract_step_from_rdf(step_uri, rdf)
            if step is None and fetch_steps:
                step = self._fetch_step(uri=step_uri)
            if step is None:
                warnings.warn(f'Could not get detailed information for '
                              f'step {step_uri}, adding a FairStep '
                              f'without attributes. This will limit '
                              f'functionality of the FairWorkflow object.')
                step = FairStep(uri=step_uri)
            self._add_step(step)

    @staticmethod
    def _extract_step_from_rdf(uri, rdf: rdflib.Graph()) -> Optional[FairStep]:
        step_rdf = rdflib.Graph()
        for s, p, o in rdf.triples((rdflib.URIRef(uri), None, None)):
            if p in FAIRSTEP_PREDICATES:
                step_rdf.add((s, p, o))
                rdf.remove((s, p, o))

        if len(step_rdf) > 0:
            return FairStep.from_rdf(step_rdf, uri=uri)
        else:
            return None

    @staticmethod
    def _fetch_step(uri: str) -> Optional[FairStep]:
        try:
            return FairStep.from_nanopub(uri=uri)
        except HTTPError as e:
            if e.response.status_code == 404:
                warnings.warn(
                    f'Failed fetching {uri} from nanopub server, probably it '
                    f'is not published there. Fairworkflows does currently not'
                    f'support other sources than nanopub')
                return None
            else:
                raise

    @property
    def first_step(self):
        """First step of workflow.

        Returns:
             First step of the workflow if existing. In weird cases (when the
             RDF has multiple first steps and is thus invalid) return a list of
             first steps.
        """
        return self.get_attribute(namespaces.PWO.hasFirstStep)

    @first_step.setter
    def first_step(self, step: FairStep):
        """
        Sets the first step of this plex workflow to the given FairStep
        """
        self.set_attribute(namespaces.PWO.hasFirstStep, rdflib.URIRef(step.uri))
        self._add_step(step)

    @property
    def unbound_inputs(self) -> List[Tuple[rdflib.URIRef, FairStep]]:
        """Get unbound inputs for workflow.

        Unbound inputs are inputs that are not outputs of any preceding step.
        You could consider them inputs for the workflow.
        """
        outputs = list()
        unbound_inputs = list()
        for step in self:
            for input in step.inputs:
                if input not in outputs:
                    unbound_inputs.append((input, step))
            outputs += step.outputs
        return unbound_inputs

    @property
    def unbound_outputs(self) -> List[Tuple[rdflib.URIRef, FairStep]]:
        """Get unbound outputs for workflow.

        Unbound outputs are outputs that are not inputs of any following
        step. You could consider them outputs of the workflow.
        """
        self._validate_inputs_and_outputs()
        inputs = list()
        unbound_outputs = list()
        for step in reversed(list(self)):
            for output in step.outputs:
                if output not in inputs:
                    unbound_outputs.append((output, step))
            inputs += step.inputs
        return unbound_outputs

    def _add_step(self, step: FairStep):
        """Add a step to workflow (low-level method)."""
        self._steps[step.uri] = step
        self._rdf.add((rdflib.URIRef(step.uri), namespaces.PPLAN.isStepOfPlan,
                       self.self_ref))
        self._last_step_added = step

    def add(self, step: FairStep, follows: FairStep = None):
        """Add a step.

        Adds the specified FairStep to the workflow rdf. If 'follows' is specified,
        then it dul:precedes the step. If 'follows' is None, the last added step (to this workflow)
        dul:precedes the step. If no steps have yet been added to the workflow, and 'follows' is None,
        then this step is automatically set to by the first step in the workflow.
        """
        if not follows:
            if self.first_step is None:
                self.first_step = step
            else:
                self.add(step, follows=self._last_step_added)
        else:
            self._rdf.add((rdflib.URIRef(follows.uri), namespaces.DUL.precedes, rdflib.URIRef(step.uri)))
            self._add_step(follows)
            self._add_step(step)

    def __iter__(self) -> Iterator[FairStep]:
        """
        Iterate over this FairWorkflow, return one step at a
        time in the order specified by the precedes relations (
        i.e. topologically sorted).

        Raises:
             RuntimeError: if we cannot sort steps based on precedes
             predicate, for example if there are 2 steps that are not
             connected to each other by the precedes predicate. We do not
             know how to sort in that case.
        """
        if len(self._steps) == 1:
            # In case of only one step we do not need to sort
            ordered_steps = [step.uri for step in self._steps.values()]
        else:
            G = nx.MultiDiGraph()
            for s, p, o in self._rdf:
                if p == namespaces.DUL.precedes:
                    G.add_edge(s, o)
            if len(G) == len(self._steps):
                ordered_steps = nx.topological_sort(G)
            else:
                raise RuntimeError('Cannot sort steps based on precedes'
                                   'predicate')
        for step_uri in ordered_steps:
            yield self.get_step(str(step_uri))

    @property
    def is_pplan_plan(self):
        """
        Returns True if this object's rdf specifies that it is a pplan:Plan
        """
        return (self.self_ref, RDF.type, namespaces.PPLAN.Plan) in self._rdf

    def get_step(self, uri):
        """
            Returns the FairStep instance associated with the given step URI (if such a step was added to this workflow)
        """
        return self._steps[uri]

    @property
    def label(self):
        """Label.

        Returns the rdfs:label of this workflow (or a list, if more than one matching triple is found)
        """
        return self.get_attribute(RDFS.label)

    @label.setter
    def label(self, value):
        """
        Adds the given text string as an rdfs:label for this FairWorkflow
        object.
        """
        self.set_attribute(RDFS.label, rdflib.term.Literal(value))

    @property
    def description(self):
        """
        Description of the workflow. This is the dcterms:description found in
        the rdf for this workflow (or a list if more than one matching triple
        found)
        """
        return self.get_attribute(DCTERMS.description)

    @description.setter
    def description(self, value):
        self.set_attribute(DCTERMS.description, rdflib.term.Literal(value))

    def validate(self):
        """Validate workflow.

        Checks whether this workflow's rdf:
         * Has sufficient information required of a workflow in the Plex
            ontology.
         * Step 'hasInputVar' and 'hasOutputVar' match with workflows 'precedes'
            predicate
        """
        conforms = True
        log = ''

        if not self.is_pplan_plan:
            log += 'Plan RDF does not say it is a pplan:Plan\n'
            conforms = False

        if not self.description:
            log += 'Plan RDF has no dcterms:description\n'
            conforms = False

        if self.first_step is None:
            log += 'Plan RDF does not specify a first step (pwo:hasFirstStep)\n'
            conforms = False

        try:
            self._validate_inputs_and_outputs()
        except AssertionError as e:
            log += str(e)
            conforms = False

        assert conforms, log

    def _validate_inputs_and_outputs(self):
        """Validate that inputs and outputs match step order.

        Assert that for all steps the input of a step is *not* the output of a
        step later in the workflow (order based on the 'precedes' predicate).

        NB: Step inputs can be unbound (and thus inputs for the workflow
        itself). Only if a later step outputs the input variable of a
        preceding step this is invalid.
        """
        outputs = list()
        unbound_inputs = list()
        for step in self:
            for input in step.inputs:
                if input not in outputs:
                    unbound_inputs.append((input, step))
            outputs += step.outputs
        invalid_inputs = [(input, step) for input, step in unbound_inputs
                          if input in outputs]

        if len(invalid_inputs) > 0:
            m = ''.join([f'{step.self_ref} has input {input} that is the '
                         f'output of a later step\n'
                         for input, step in invalid_inputs])
            raise AssertionError(m)

    @staticmethod
    def _import_graphviz():
        """Import graphviz.

        Raises:
             ImportError with appropriate message if import failed
        """
        try:
            import graphviz
            return graphviz
        except ImportError:
            raise ImportError('Cannot produce visualization of RDF, you need '
                              'to install graphviz python package. '
                              'Version 0.14.1 is known to work well.')

    def display(self):
        """Visualize workflow directly in notebook."""
        graphviz = self._import_graphviz()

        with TemporaryDirectory() as td:
            filename = Path(td) / 'dag.dot'
            with open(filename, 'w') as f:
                rdf2dot(self._rdf, f)
            return graphviz.Source.from_file(filename)

    def draw(self, filepath):
        """Visualize workflow.

        Writes a .dot file and a .dot.png file of the workflow
        visualization based on filepath argument. Use the .dot file to create
        different renderings of the visualization using Graphviz library. The
        .dot.png file is one of those renderings.
        """

        graphviz = self._import_graphviz()
        filepath = filepath.split('.')[0] + '.dot'
        with open(filepath, 'w') as f:
            rdf2dot(self._rdf, f)

        try:
            graphviz.render('dot', 'png', filepath)
        except graphviz.ExecutableNotFound:
            raise RuntimeError(
                'Cannot produce visualization of RDF, you need to install '
                'graphviz dependency https://graphviz.org/')

    def __str__(self):
        """
            Returns string representation of this FairWorkflow object.
        """
        s = f'Workflow URI = {self._uri}\n'
        s += self._rdf.serialize(format='trig').decode('utf-8')
        return s


def add_step(fw: FairWorkflow):
    """
    Decorator that, upon execution, will convert a function to a FairStep, and add it to the
    given FairWorkflow, 'fw'
    """

    def decorated_step(function):

        def wrapped_step(*args, **kwargs):
            fw.add(FairStep.from_function(function=function))
            function(*args, **kwargs)

        return wrapped_step

    return decorated_step
