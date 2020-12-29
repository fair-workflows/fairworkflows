import warnings
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator, Tuple, List, Optional

import networkx as nx
import rdflib
from rdflib import RDF, RDFS, DCTERMS
from rdflib.tools.rdf2dot import rdf2dot
from requests import HTTPError

from fairworkflows import namespaces
from fairworkflows.fairstep import FairStep, FAIRSTEP_PREDICATES
from fairworkflows.rdf_wrapper import RdfWrapper, replace_in_rdf


class FairWorkflow(RdfWrapper):

    """
        Class for building, validating and publishing Fair Workflows, as described by the plex ontology in the publication:

        Celebi, R., Moreira, J. R., Hassan, A. A., Ayyar, S., Ridder, L., Kuhn, T., & Dumontier, M. (2019). Towards FAIR protocols and workflows: The OpenPREDICT case study. arXiv preprint arXiv:1911.09531.

        Fair Workflows may be fetched from Nanopublications, or created through the addition of FairStep's.
    """

    def __init__(self, description: str = None, label: str = None, uri=None,
                 is_pplan_plan: bool = True, first_step: FairStep = None):
        super().__init__(uri=uri, ref_name='plan')
        self._is_published = False
        self.is_pplan_plan = is_pplan_plan
        if description is not None:
            self.description = description
        if label is not None:
            self.label = label
        self._steps = {}
        self._last_step_added = None
        if first_step is not None:
            self.first_step = first_step
        self._is_modified = False

    @classmethod
    def from_rdf(cls, rdf: rdflib.Graph, uri: str,
                 fetch_references: bool = False, force: bool = False,
                 remove_irrelevant_triples: bool = True):
        """Construct Fair Workflow from existing RDF.

        Args:
            rdf: RDF graph containing information about the workflow and
                possibly it's associated steps. Should use plex ontology.
            uri: URI of the workflow
            fetch_references: toggles fetching steps. I.e. if we encounter steps
                that are part of the workflow, but are not specified in the
                RDF we try fetching them from nanopub
            force: Toggle forcing creation of object even if url is not in any of the subjects of
                the passed RDF
            remove_irrelevant_triples: Toggle removing irrelevant triples for this FairWorkflow.
        """
        rdf = deepcopy(rdf)  # Make sure we don't mutate user RDF
        cls._uri_is_subject_in_rdf(uri, rdf, force=force)
        self = cls(uri=uri)
        self._extract_steps(rdf, uri, fetch_references)
        if remove_irrelevant_triples:
            self._rdf = self._get_relevant_triples(uri, rdf)
        else:
            self._rdf = deepcopy(rdf)  # Make sure we don't mutate user RDF
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
    def _get_relevant_triples(uri, rdf):
        """
        Select only relevant triples from RDF using the following heuristics:
        * Match all triples that are through an arbitrary-length property path related to the
            workflow uri. So if 'URI predicate Something', then all triples 'Something predicate
            object' are selected, and so forth.
        NB: We assume that all step-related triples are already extracted by the _extract_steps
        method
        """
        q = """
        SELECT ?s ?p ?o
        WHERE {
            ?s ?p ?o .
            # Match all triples that are through an arbitrary-length property path related to the
            # workflow uri. (a|!a) matches all predicates. Binding to workflow_uri is done when
            # executing.
            ?workflow_uri (a|!a)+ ?o .
        }
        """
        g = rdflib.Graph(namespace_manager=rdf.namespace_manager)
        for triple in rdf.query(q, initBindings={'workflow_uri': rdflib.URIRef(uri)}):
            g.add(triple)
        return g

    @staticmethod
    def _extract_step_from_rdf(uri, rdf: rdflib.Graph()) -> Optional[FairStep]:
        relevant_triples = FairStep._get_relevant_triples(uri, rdf)
        step_rdf = rdflib.Graph()
        for triple in relevant_triples:
            step_rdf.add(triple)
            rdf.remove(triple)

        if len(step_rdf) > 0:
            return FairStep.from_rdf(step_rdf, uri=uri, remove_irrelevant_triples=True)
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
                raise RuntimeError('Cannot sort steps based on precedes '
                                   'predicate')
        for step_uri in ordered_steps:
            yield self.get_step(str(step_uri))

    @property
    def is_pplan_plan(self):
        """
        Returns True if this object's rdf specifies that it is a pplan:Plan
        """
        return (self.self_ref, RDF.type, namespaces.PPLAN.Plan) in self._rdf

    @is_pplan_plan.setter
    def is_pplan_plan(self, value:bool):
        """
        Adds/removes the pplan:Plan triple from the RDF, in accordance with the provided boolean.
        """
        if value is True:
            if self.is_pplan_plan is False:
                self.set_attribute(RDF.type, namespaces.PPLAN.Plan, overwrite=False)
        elif value is False:
            if self.is_pplan_plan is True:
                self.remove_attribute(RDF.type, object=namespaces.PPLAN.Plan)

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

    def validate(self, shacl=False):
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

        if not self.label:
            log += 'Plan RDF has no rdfs:label\n'
            conforms = False

        if self.first_step is None:
            log += 'Plan RDF does not specify a first step (pwo:hasFirstStep)\n'
            conforms = False

        assert conforms, log

        # Now validate against the PLEX shacl shapes file, if requested
        if shacl:
            self.shacl_validate()

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

    def publish_as_nanopub(self, use_test_server=False, **kwargs):
        """Publish to nanopub server.

        First publish the steps, use the URIs of the published steps in the workflow. Then
        publish the workflow.

        Args:
            use_test_server (bool): Toggle using the test nanopub server.
            kwargs: Keyword arguments to be passed to [nanopub.Publication.from_assertion](
                https://nanopub.readthedocs.io/en/latest/reference/publication.html#
                nanopub.publication.Publication.from_assertion).
                This allows for more control over the nanopublication RDF.

        Returns:
            a dictionary with publication info, including 'nanopub_uri', and 'concept_uri' of the
                published workflow
        """
        for step in self:
            if step.is_modified or not step._is_published:
                self._is_modified = True  # If one of the steps is modified the workflow is too.
                old_uri = step.uri
                step.publish_as_nanopub(use_test_server=use_test_server, **kwargs)
                published_step_uri = step.uri
                replace_in_rdf(self.rdf, oldvalue=rdflib.URIRef(old_uri),
                               newvalue=rdflib.URIRef(published_step_uri))
                del self._steps[old_uri]
                self._steps[published_step_uri] = step
        return self._publish_as_nanopub(use_test_server=use_test_server, **kwargs)

    def __str__(self):
        """
            Returns string representation of this FairWorkflow object.
        """
        s = f'Workflow URI = {self._uri}\n'
        s += self._rdf.serialize(format='trig').decode('utf-8')
        return s

