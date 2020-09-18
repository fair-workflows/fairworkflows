from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator, Tuple, List

import networkx as nx
import rdflib
from rdflib import RDF, DCTERMS
from rdflib.tools.rdf2dot import rdf2dot

from .fairstep import FairStep
from .nanopub import Nanopub
from .rdf_wrapper import RdfWrapper

DEFAULT_PLAN_URI = 'http://purl.org/nanopub/temp/mynanopub#plan'


class FairWorkflow(RdfWrapper):

    """
        Class for building, validating and publishing Fair Workflows, as described by the plex ontology in the publication:

        Celebi, R., Moreira, J. R., Hassan, A. A., Ayyar, S., Ridder, L., Kuhn, T., & Dumontier, M. (2019). Towards FAIR protocols and workflows: The OpenPREDICT case study. arXiv preprint arXiv:1911.09531.

        Fair Workflows may be fetched from Nanopublications, or created through the addition of FairStep's.
    """

    def __init__(self, description, uri=DEFAULT_PLAN_URI):
        super().__init__(uri=uri)
        self._rdf.add((self.self_ref, RDF.type, Nanopub.PPLAN.Plan))
        self.description = description
        self._steps = {}
        self._last_step_added = None

    @property
    def first_step(self):
        """First step of workflow.

        Returns:
             First step of the workflow if existing. In weird cases (when the
             RDF has multiple first steps and is thus invalid) return a list of
             first steps.
        """
        return self.get_attribute(Nanopub.PWO.hasFirstStep)

    @first_step.setter
    def first_step(self, step: FairStep):
        """
        Sets the first step of this plex workflow to the given FairStep
        """
        self.set_attribute(Nanopub.PWO.hasFirstStep, rdflib.URIRef(step.uri))
        self._steps[step.uri] = step
        self._last_step_added = step

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

    def add(self, step:FairStep, follows:FairStep=None):
        """
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
            self._rdf.add( (rdflib.URIRef(follows.uri), Nanopub.DUL.precedes, rdflib.URIRef(step.uri)) )
            self._steps[step.uri] = step
            self._last_step_added = step

    def __iter__(self) -> Iterator[FairStep]:
        """
        Iterate over this FairWorkflow, return one step at a
        time in the order specified by the precedes relations (
        i.e. topologically sorted).
        """
        G = nx.MultiDiGraph()
        for s, p, o in self._rdf:
            if p == Nanopub.DUL.precedes:
                G.add_edge(s, o)
        for step_uri in nx.topological_sort(G):
            yield self.get_step(str(step_uri))

    @property
    def is_pplan_plan(self):
        """
        Returns True if this object's rdf specifies that it is a pplan:Plan
        """
        return (self.self_ref, RDF.type, Nanopub.PPLAN.Plan) in self._rdf

    def get_step(self, uri):
        """
            Returns the FairStep instance associated with the given step URI (if such a step was added to this workflow)
        """
        return self._steps[uri]

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
