import inspect
import io
import logging
import warnings
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator, Optional, Callable

import nanopub
import networkx as nx
import noodles
import rdflib
from noodles.interface import PromisedObject
from rdflib import RDF, RDFS, DCTERMS
from rdflib.tools.rdf2dot import rdf2dot
from requests import HTTPError

from fairworkflows import namespaces
from fairworkflows.fairstep import FairStep
from fairworkflows.rdf_wrapper import RdfWrapper


class FairWorkflow(RdfWrapper):

    """
        Class for building, validating and publishing Fair Workflows, as described by the plex ontology in the publication:

        Celebi, R., Moreira, J. R., Hassan, A. A., Ayyar, S., Ridder, L., Kuhn, T., & Dumontier, M. (2019). Towards FAIR protocols and workflows: The OpenPREDICT case study. arXiv preprint arXiv:1911.09531.

        Fair Workflows may be fetched from Nanopublications, or created through the addition of FairStep's.
    """

    def __init__(self, description: str = None, label: str = None, uri=None,
                 is_pplan_plan: bool = True, first_step: FairStep = None, derived_from=None):
        super().__init__(uri=uri, ref_name='plan', derived_from=derived_from)
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
                that are part of the workflow we try fetching them from nanopub
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

    @classmethod
    def from_function(cls, func: Callable):
        """
        Return a FairWorkflow object for a function decorated with is_fairworkflow decorator
        """
        try:
            return func._fairworkflow
        except AttributeError:
            raise ValueError('The function was not marked as a fair workflow,'
                             'use is_fairworkflow decorator to mark it.')

    @classmethod
    def from_noodles_promise(cls, workflow_level_promise, step_level_promise, description: str = None, label: str =
                             None, is_pplan_plan: bool = True, derived_from=None):
        """

        Args:
            workflow_level_promise: Noodles workflow_level_promise at the workflow function level.
                This excludes the individual steps, but we need it to do proper execution.
            step_level_promise: Promise at the steps level. This includes the individual steps as
                nodes but does not bind them together. We use this to extract step information from
                it.
        """
        self = cls(description=description, label=label, is_pplan_plan=is_pplan_plan, derived_from=derived_from)
        self.workflow_level_promise = workflow_level_promise

        workflow = noodles.get_workflow(step_level_promise)

        steps_dict = {i: n.foo._fairstep for i, n in workflow.nodes.items()}

        for i, step in steps_dict.items():
            self._add_step(step)

        for i in workflow.links:
            current_step = steps_dict[i]
            from_uri = rdflib.URIRef(steps_dict[i].uri + '#' + current_step.outputs[0].name)
            for j in workflow.links[i]:
                linked_step = steps_dict[j[0]]
                linked_var_name = str(j[1].name)
                to_uri = rdflib.URIRef(linked_step.uri + '#' + linked_var_name)
                self._rdf.add((from_uri, namespaces.PPLAN.bindsTo, to_uri))

                precedes_triple = (rdflib.URIRef(current_step.uri), namespaces.DUL.precedes, rdflib.URIRef(linked_step.uri))
                if precedes_triple not in self._rdf:
                    self._rdf.add(precedes_triple)

            if len(workflow.links[i]) == 0:
                to_uri = rdflib.BNode('result')
                self._rdf.add((from_uri, namespaces.PPLAN.bindsTo, to_uri))

        return self

    def _extract_steps(self, rdf, uri, fetch_steps=True):
        """Extract FairStep objects from rdf.

        Create FairStep objects for all steps in the passed RDF.
        Optionally try to fetch steps from nanopub.
        """
        step_refs = rdf.subjects(predicate=namespaces.PPLAN.isStepOfPlan,
                                 object=rdflib.URIRef(uri))
        for step_ref in step_refs:
            step_uri = str(step_ref)
            step = None
            if fetch_steps:
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
        CONSTRUCT { ?s ?p ?o }
        WHERE {
            ?s ?p ?o .
            # Match all triples that are through an arbitrary-length property path related to the
            # workflow uri. (<>|!<>) matches all predicates. Binding to workflow_uri is done when
            # executing.
            ?workflow_uri (<>|!<>)* ?s .
        }
        """
        g = rdflib.Graph(namespace_manager=rdf.namespace_manager)
        for triple in rdf.query(q, initBindings={'workflow_uri': rdflib.URIRef(uri)}):
            g.add(triple)
        return g

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
        step.register_workflow(self)

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

    def display(self, full_rdf=False):
        """Visualize workflow directly in notebook."""

        if full_rdf:
            return self.display_full_rdf()
        else:
            if not hasattr(self, 'workflow_level_promise'):
                raise ValueError('Cannot display workflow as no noodles step_level_promise has been constructed.')
            import noodles.tutorial
            noodles.tutorial.display_workflows(prefix='control', workflow=self.workflow_level_promise)

    def display_full_rdf(self):
        graphviz = self._import_graphviz()

        with TemporaryDirectory() as td:
            filename = Path(td) / 'dag.dot'
            with open(filename, 'w') as f:
                rdf2dot(self._rdf, f)
            return graphviz.Source.from_file(filename)

    def execute(self, *args, **kwargs):
        """
        Executes the workflow on the specified number of threads. Noodles is used as the execution
        engine. If a noodles workflow has not been generated for this fairworkflow object, then
        it cannot be executed and an exception will be raised.

        Returns a tuple (result, retroprov), where result is the final output of the executed
        workflow and retroprov is the retrospective provenance logged during execution.
        """

        if not hasattr(self, 'workflow_level_promise'):
            raise ValueError('Cannot execute workflow as no noodles step_level_promise has been constructed.')

        log = io.StringIO()
        log_handler = logging.StreamHandler(log)
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        log_handler.setFormatter(formatter)

        logger = logging.getLogger('noodles')
        logger.setLevel(logging.INFO)
        logger.handlers = [log_handler]
        self.workflow_level_promise = noodles.workflow.from_call(
            noodles.get_workflow(self.workflow_level_promise).root_node.foo, args, kwargs, {})
        result = noodles.run_single(self.workflow_level_promise)

        # Generate the retrospective provenance as a (nano-) Publication object
        retroprov = self._generate_retrospective_prov_publication(log.getvalue())

        return result, retroprov

    def _generate_retrospective_prov_publication(self, log:str) -> nanopub.Publication:
        """
        Utility method for generating a Publication object for the retrospective
        provenance of this workflow. Uses the given 'log' string as the actual
        provenance for now.
        """
        log_message = rdflib.Literal(log)
        this_retroprov = rdflib.BNode('retroprov')
        if self.uri is None or self.uri == 'None': # TODO: This is horrific
            this_workflow = rdflib.URIRef('http://www.example.org/unpublishedworkflow')
        else:
            this_workflow = rdflib.URIRef(self.uri)

        retroprov_assertion = rdflib.Graph()
        retroprov_assertion.add((this_retroprov, rdflib.RDF.type, namespaces.PROV.Activity))
        retroprov_assertion.add((this_retroprov, namespaces.PROV.wasDerivedFrom, this_workflow))
        retroprov_assertion.add((this_retroprov, RDFS.label, log_message))
        retroprov = nanopub.Publication.from_assertion(assertion_rdf=retroprov_assertion)

        return retroprov


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

        Publish the workflow as nanopublication to the nanopub server.

        Raises:
            RuntimeError: If one of the steps of the workflow was not published yet.

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
                raise RuntimeError(f'{step} was not published yet, please publish steps first')

        return self._publish_as_nanopub(use_test_server=use_test_server, **kwargs)

    def __str__(self):
        """
            Returns string representation of this FairWorkflow object.
        """
        s = f'Workflow URI = {self._uri}\n'
        s += self._rdf.serialize(format='trig').decode('utf-8')
        return s


def is_fairworkflow(label: str = None, is_pplan_plan: bool = True):
    """Mark a function as returning a FAIR workflow.

    Use as decorator to mark a function as a FAIR workflow. Set properties of the fair workflow using
    arguments to the decorator.

    The raw code of the function will be used to set the description of the fair workflow.

    The type annotations of the input arguments and return statement will be used to
    automatically set inputs and outputs of the FAIR workflow.

    Args:
        label (str): Label of the fair workflow (corresponds to rdfs:label predicate)
        is_pplan_plan (str): Denotes whether this workflow is a pplan:Plan

    """
    def _modify_function(func):
        """
        Store FairWorkflow as _fairworkflow attribute of the function. Use inspection to get the
        description, inputs, and outputs of the workflow based on the function specification.
        Call the scheduled_workflow with empty arguments so we get a PromisedObject. These empty
        arguments will be replaced upon execution with the input arguments that the .execute()
        method is called with.
        """
        scheduled_workflow = noodles.schedule(func)
        num_params = len(inspect.signature(func).parameters)
        empty_args = ([inspect.Parameter.empty()] * num_params)
        workflow_level_promise = scheduled_workflow(*empty_args)
        _validate_decorated_function(func, empty_args)
        step_level_promise = func(*empty_args)

        # Description of workflow is the raw function code
        description = inspect.getsource(func)
        workflow_level_promise._fairworkflow = FairWorkflow.from_noodles_promise(
            workflow_level_promise, step_level_promise, description=description, label=label,
            is_pplan_plan=is_pplan_plan, derived_from=None)
        return workflow_level_promise
    return _modify_function


def _validate_decorated_function(func, empty_args):
    """
    Validate that a function decorated with is_fairworkflow actually consists of steps that are
    decorated with is_fairstep. Call the function using empty arguments to test. NB: This won't
    catch all edgecases of users misusing the is_fairworkflow decorator, but at least will
    provide more useful error messages in frequently occurring cases.
    """
    try:
        result = func(*empty_args)
    except TypeError as e:
        raise TypeError("Marking the function as workflow with `is_fairworkflow` decorator "
                        "failed. "
                        "Did you use the is_fairstep decorator on all the steps? "
                        f"Detailed error message: {e}")
    if not isinstance(result, PromisedObject):
        raise TypeError("The workflow does not return a 'promise'. Did you use the "
                        "is_fairstep decorator on all the steps?")
