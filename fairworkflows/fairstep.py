import inspect
import typing
from copy import deepcopy
from typing import Callable, get_type_hints, List, Union
from urllib.parse import urldefrag

import noodles
import rdflib
from rdflib import RDF, RDFS, DCTERMS

from fairworkflows import namespaces
from fairworkflows.config import DUMMY_FAIRWORKFLOWS_URI
from fairworkflows.rdf_wrapper import RdfWrapper, replace_in_rdf

class FairVariable:
    """Represents a variable.

    The variable corresponds to an RDF blank node of the same name, that has an RDF:type,
    (PPLAN:Variable), and an RDFS:comment - a string literal representing the type (i.e.
    int, str, float) of the variable.

    The FairVariable is normally associated with a FairStep by a PPLAN:hasInputVar or
    PPLAN:hasOutputVar predicate.

    Args:
        name: The name of the variable (and of the blank node in RDF that this variable is
            represented with)
        uri: Optionally pass a uri that the variable is referred to, the variable name will be
            automatically extracted from it. This argument is usually only used when we extract a
            variable from rdf)
        computational_type: The computational type of the variable (i.e. int, str, float etc.). For
                            now these are just strings of the python type name, but in future should
                            become mapped to e.g. XSD types.
        semantic_types: One or more URIs that describe the semantic type(s) of this FairVariable.
    """
    def __init__(self, name: str = None, computational_type: str = None, semantic_types = None, uri: str = None):
        if uri and name is None:
            # Get the name from the uri (i.e. 'input1' from http://example.org#input1)
            _, name = urldefrag(uri)
        self.name = name
        self.computational_type = computational_type

        if semantic_types is None:
            self.semantic_types = []
        else:
            if isinstance(semantic_types, str) or isinstance(semantic_types, rdflib.URIRef):
                self.semantic_types = [rdflib.URIRef(semantic_types)]
            else:
                self.semantic_types = [rdflib.URIRef(t) for t in semantic_types]

    def __eq__(self, other):
        return self.name == other.name and self.computational_type == other.computational_type

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        return f'FairVariable {self.name} of computational type: {self.computational_type} and semantic types: {self.semantic_types}'


class FairStep(RdfWrapper):
    """Represent a step in a fair workflow.

    Class for building, validating and publishing Fair Steps,
    as described by the plex ontology in the publication:
    Celebi, R., Moreira, J. R., Hassan, A. A., Ayyar, S., Ridder, L., Kuhn, T.,
    & Dumontier, M. (2019). Towards FAIR protocols and workflows: T
    he OpenPREDICT case study. arXiv preprint arXiv:1911.09531.

    Fair Steps may be fetched from Nanopublications, created from rdflib
    graphs or python functions.

    Attributes:
        label (str): Label of the fair step (corresponds to rdfs:label predicate)
        description (str): Description of the fair step (corresponding to dcterms:description)
        uri (str): URI depicting the step.
        is_pplan_step (str): Denotes whether this step is a pplan:Step
        is_manual_task (str): Denotes whether this step is a bpmn.ManualTask
        is_script_task (str): Denotes whether this step is a bpmn.ScriptTask
        inputs (list of FairVariable objects): The inputs of the step (corresponding to
            pplan:hasInputVar).
        outputs (list of FairVariable objects): The outputs of the step (corresponding to
            pplan:hasOutputVar).
    """

    def __init__(self, label: str = None, description: str = None, uri=None,
                 is_pplan_step: bool = True, is_manual_task: bool = None,
                 is_script_task: bool = None, inputs: List[FairVariable] = None,
                 outputs: List[FairVariable] = None, derived_from=None):
        super().__init__(uri=uri, ref_name='step', derived_from=derived_from)
        if label is not None:
            self.label = label
        if description is not None:
            self.description = description
        self.is_pplan_step = is_pplan_step
        if is_script_task and is_manual_task:
            ValueError('A fair step cannot be both a manual and a script task, at least one of'
                       'is_fair_step and is_script_task must be False')
        if is_manual_task is not None:
            self.is_manual_task = is_manual_task
        if is_script_task is not None:
            self.is_script_task = is_script_task
        if inputs is not None:
            self.inputs = inputs
        if outputs is not None:
            self.outputs = outputs
        # Set temporary URI to refer to this step in workflows
        # (i.e. 'http://fairworkflows.org#8769029329049')
        if uri is None:
            self._uri = DUMMY_FAIRWORKFLOWS_URI + '#step' + str(hash(self))

        self._is_modified = False
        self._workflows = set()

    @classmethod
    def from_rdf(cls, rdf, uri, fetch_references: bool = False, force: bool = False,
                 remove_irrelevant_triples: bool = True):
        """Construct Fair Step from existing RDF.

        Args:
            rdf: The RDF graph
            uri: Uri of the object
            fetch_references: Boolean toggling whether to fetch objects from nanopub that are
                referred by this object. For a FairStep there are currently no references supported.
            force: Toggle forcing creation of object even if url is not in any of the subjects of
                the passed RDF
            remove_irrelevant_triples: Toggle removing irrelevant triples for this Step. This
                uses heuristics that might not work for all passed RDF graphs.
        """
        cls._uri_is_subject_in_rdf(uri, rdf, force=force)
        self = cls(uri=uri)
        if remove_irrelevant_triples:
            self._rdf = self._get_relevant_triples(uri, rdf)
        else:
            self._rdf = deepcopy(rdf)  # Make sure we don't mutate user RDF
        self.anonymise_rdf()
        return self

    @staticmethod
    def _get_relevant_triples(uri, rdf):
        """
        Select only relevant triples from RDF using the following heuristics:
        * Filter out the DUL:precedes and PPLAN:isStepOfPlan predicate triples, because they are
            part of a workflow and not of a step.
        * Match all triples that are through an arbitrary-length property path related to the
            step uri. So if 'URI predicate Something', then all triples 'Something predicate
            object' are selected, and so forth.
        """
        # Remove workflow-related triples from the graph, they effectively make other steps or
        # the whole workflow 'children' of a step so it is important to to this before the query
        # TODO:  This would be neater to do in a subquery.
        rdf = deepcopy(rdf)
        rdf.remove((None, namespaces.DUL.precedes, None))
        rdf.remove((None, namespaces.PPLAN.isStepOfPlan, None))
        q = """
        CONSTRUCT { ?s ?p ?o }
        WHERE {
            ?s ?p ?o .
            # Match all triples that are through an arbitrary-length property path related to the
            # step uri. (<>|!<>) matches all predicates. Binding to step_uri is done when executing.
            ?step_uri (<>|!<>)* ?s .
        }
        """
        g = rdflib.Graph(namespace_manager=rdf.namespace_manager)
        for triple in rdf.query(q, initBindings={'step_uri': rdflib.URIRef(uri)}):
            g.add(triple)
        return g

    @classmethod
    def from_function(cls, func: Callable):
        """
        Generates a plex rdf decription for the given python function,
        and makes this FairStep object a bpmn:ScriptTask.
        """
        try:
            return func._fairstep
        except AttributeError:
            raise ValueError('The function was not marked as a fair step,'
                             'use mark_as_fairstep decorator to mark it.')

    @property
    def is_pplan_step(self):
        """Return True if this FairStep is a pplan:Step, else False."""
        return (self.self_ref, RDF.type, namespaces.PPLAN.Step) in self._rdf

    @is_pplan_step.setter
    def is_pplan_step(self, value: bool):
        """
        Adds/removes the pplan:Step triple from the RDF, in accordance with the provided boolean.
        """
        if value:
            if not self.is_pplan_step:
                self.set_attribute(RDF.type, namespaces.PPLAN.Step, overwrite=False)
        else:
            self.remove_attribute(RDF.type, object=namespaces.PPLAN.Step)

    @property
    def is_manual_task(self):
        """Returns True if this FairStep is a bpmn:ManualTask, else False."""
        return (self.self_ref, RDF.type, namespaces.BPMN.ManualTask) in self._rdf

    @is_manual_task.setter
    def is_manual_task(self, value: bool):
        """
        Adds/removes the manual task triple to the RDF, in accordance with the provided boolean.
        """
        if value:
            if not self.is_manual_task:
                self.set_attribute(RDF.type, namespaces.BPMN.ManualTask, overwrite=False)
            self.is_script_task = False  # manual and script are mutually exclusive
        else:
            self.remove_attribute(RDF.type, object=namespaces.BPMN.ManualTask)

    @property
    def is_script_task(self):
        """Returns True if this FairStep is a bpmn:ScriptTask, else False."""
        return (self.self_ref, RDF.type, namespaces.BPMN.ScriptTask) in self._rdf

    @is_script_task.setter
    def is_script_task(self, value: bool):
        """
        Adds/removes the script task triple to the RDF, in accordance with the provided boolean.
        """
        if value:
            if not self.is_script_task:
                self.set_attribute(RDF.type, namespaces.BPMN.ScriptTask, overwrite=False)
            self.is_manual_task = False  # manual and script are mutually exclusive
        else:
            self.remove_attribute(RDF.type, object=namespaces.BPMN.ScriptTask)

    def _get_variable(self, var_ref: Union[rdflib.term.BNode, rdflib.URIRef]) -> FairVariable:
        """Retrieve a specific FairVariable from the RDF triples."""
        rdfs_comment_objs = list(self._rdf.objects(var_ref, RDFS.comment))
        computational_type = str(rdfs_comment_objs[0])

        # Get all semantic types of this FairVariable, excluding PPLAN.Variable
        sem_type_objs = self._rdf.objects(var_ref, RDF.type)
        sem_types = [sem_type for sem_type in sem_type_objs if sem_type != namespaces.PPLAN.Variable]

        if isinstance(var_ref, rdflib.term.BNode):
            return FairVariable(name=str(var_ref), computational_type=computational_type, semantic_types=sem_types)
        else:
            return FairVariable(uri=str(var_ref), computational_type=computational_type, semantic_types=sem_types)

    def _add_variable(self, variable: FairVariable, relation_to_step):
        """Add triples describing FairVariable to rdf."""
        var_ref = rdflib.term.BNode(variable.name)
        self.set_attribute(relation_to_step, var_ref, overwrite=False)
        self._rdf.add((var_ref, RDFS.comment, rdflib.term.Literal(variable.computational_type)))
        self._rdf.add((var_ref, RDF.type, namespaces.PPLAN.Variable))
        self._rdf.add((var_ref, RDFS.label, rdflib.term.Literal(variable.name)))
        for sem_var in variable.semantic_types:
            self._rdf.add((var_ref, RDF.type, sem_var))

    @property
    def inputs(self) -> List[FairVariable]:
        """Inputs for this step.

        Inputs are a list of FairVariable objects. They correspond to triples in the RDF:
        The name is stored as a blanknode with a hasInputVar relation to the step.
        This blanknode has an RDF:type, PPLAN:Variable; and an RDFS:comment, a string literal
        representing the type (i.e. int, str, float) of the variable.
        """
        return [self._get_variable(var_ref) for var_ref
                in self.get_attribute(namespaces.PPLAN.hasInputVar, return_list=True)]

    @inputs.setter
    def inputs(self, variables: List[FairVariable]):
        self.remove_attribute(namespaces.PPLAN.hasInputVar)
        for variable in variables:
            self._add_variable(variable, namespaces.PPLAN.hasInputVar)

    @property
    def outputs(self) -> List[FairVariable]:
        """Outputs for this step.

        Outputs are a list of FairVariable objects. They correspond to triples in the RDF:
        The name is stored as a blanknode with a hasOutputVar relation to the step.
        This blanknode has an RDF:type, PPLAN:Variable; and an RDFS:comment, a string literal
        representing the type (i.e. int, str, float) of the variable.
        """
        return [self._get_variable(var_ref) for var_ref
                in self.get_attribute(namespaces.PPLAN.hasOutputVar, return_list=True)]

    @outputs.setter
    def outputs(self, variables: List[FairVariable]):
        self.remove_attribute(namespaces.PPLAN.hasOutputVar)
        for variable in variables:
            self._add_variable(variable, namespaces.PPLAN.hasOutputVar)

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

    def validate(self, shacl=False):
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

        # Now validate against the PLEX shacl shapes file, if requested
        if shacl:
            self.shacl_validate()

    def register_workflow(self, workflow):
        """Register workflow that this step is part of."""
        self._workflows.add(workflow)

    def _update_registered_workflows(self):
        """Update the workflows that this step is part of.
        NB: it could be that a step was deleted from a workflow
        """
        self._workflows = {workflow for workflow in self._workflows
                           if self in workflow}

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
        self._update_registered_workflows()
        old_uri = self.uri
        self._publish_as_nanopub(use_test_server=use_test_server, **kwargs)
        var_names = [var.name for var in (self.inputs + self.outputs)]
        for workflow in self._workflows:
            replace_in_rdf(workflow.rdf, oldvalue=rdflib.URIRef(old_uri),
                           newvalue=rdflib.URIRef(self.uri))

            # Similarly replace old URIs for variable name bindings
            published_step_uri_defrag, _ = urldefrag(self.uri)
            for var_name in var_names:
                old_var_uri = old_uri + '#' + var_name
                new_var_uri = published_step_uri_defrag + '#' + var_name
                replace_in_rdf(self.rdf, oldvalue=rdflib.URIRef(old_var_uri),
                               newvalue=rdflib.URIRef(new_var_uri))
            del workflow._steps[old_uri]
            workflow._steps[self.uri] = self

    def __str__(self):
        """
            Returns string representation of this FairStep object.
        """
        s = f'Step URI = {self._uri}\n'
        s += self._rdf.serialize(format='trig').decode('utf-8')
        return s


def is_fairstep(label: str = None, is_pplan_step: bool = True, is_manual_task: bool = False,
                     is_script_task: bool = True, **kwargs):
    """Mark a function as a FAIR step to be used in a fair workflow.

    Use as decorator to mark a function as a FAIR step. Set properties of the fair step using
    arguments to the decorator.

    The raw code of the function will be used to set the description of the fair step.

    The type annotations of the input arguments and return statement will be used to
    automatically set inputs and outputs of the FAIR step.

    Args:
        label (str): Label of the fair step (corresponds to rdfs:label predicate)
        is_pplan_step (str): Denotes whether this step is a pplan:Step
        is_manual_task (str): Denotes whether this step is a bpmn.ManualTask
        is_script_task (str): Denotes whether this step is a bpmn.ScriptTask

    All additional arguments are expected to correspond to input parameters of the decorated
    function, and are used to provide extra semantic types for that parameter. For example,
    consider the following decorated function:
        @is_fairstep(label='Addition', a='http://www.example.org/number', out1='http://www.example.org/float')
        def add(a:float, b:float) -> float:
            return a + b
    1. Note that using 'a' as parameter to the decorator allows the user to provide a URI for a semantic type
    that should be associated with the function's input parameter, 'a'. This can be either a string, an
    rdflib.URIRef, or a list of these.
    2. Note that the return parameter is referred to using 'out1', because it does not otherwise have a name.
    In this case, the function only returns one value. However, if e.g. a tuple of 3 values were returned,
    you could use out1, out2 and out3 to set the semantic types of each return value, if so desired.
    """

    def _modify_function(func):
        """
        Store FairStep object as _fairstep attribute of the function. Use inspection to get the
        description, inputs, and outputs of the step based on the function specification.

        Returns this function decorated with the noodles schedule decorator.
        """
        # Description of step is the raw function code
        description = inspect.getsource(func)
        inputs = _extract_inputs_from_function(func, kwargs)
        outputs = _extract_outputs_from_function(func, kwargs)


        func._fairstep = FairStep(uri='http://www.example.org/unpublished-'+func.__name__,
                                  label=label,
                                  description=description,
                                  is_pplan_step=is_pplan_step,
                                  is_manual_task=is_manual_task,
                                  is_script_task=is_script_task,
                                  inputs=inputs,
                                  outputs=outputs)

        return noodles.schedule(func)

    return _modify_function


def _extract_inputs_from_function(func, additional_params) -> List[FairVariable]:
    """
    Extract inputs from function using inspection. The name of the argument will be the name of
    the fair variable, the corresponding type hint will be the type of the variable.
    """
    argspec = inspect.getfullargspec(func)
    try:
        return [FairVariable(
                    name=arg,
                    computational_type=argspec.annotations[arg].__name__,
                    semantic_types=additional_params.get(arg))
                    for arg in argspec.args]
    except KeyError:
        raise ValueError('Not all input arguments have type hinting, '
                         'FAIR step functions MUST have type hinting, '
                         'see https://docs.python.org/3/library/typing.html')


def _extract_outputs_from_function(func, additional_params) -> List[FairVariable]:
    """
    Extract outputs from function using inspection. The name will be {function_name}_output{
    output_number}. The corresponding return type hint will be the type of the variable.
    """
    annotations = get_type_hints(func)
    try:
        return_annotation = annotations['return']
    except KeyError:
        raise ValueError('The return of the function does not have type hinting, '
                         'FAIR step functions MUST have type hinting, '
                         'see https://docs.python.org/3/library/typing.html')
    if _is_generic_tuple(return_annotation):
        return [FairVariable(
                    name='out' + str(i + 1),
                    computational_type=annotation.__name__,
                    semantic_types=additional_params.get('out' + str(i + 1)))
                for i, annotation in enumerate(return_annotation.__args__)]
    else:
        return [FairVariable(
                name='out1',
                computational_type=return_annotation.__name__,
                semantic_types=additional_params.get('out1'))]


def _is_generic_tuple(type_):
    """
    Check whether a type annotation is Tuple
    """
    if hasattr(typing, '_GenericAlias'):
        # 3.7
        # _GenericAlias cannot be imported from typing, because it doesn't
        # exist in all versions, and it will fail the type check in those
        # versions as well, so we ignore it.
        return (isinstance(type_, typing._GenericAlias)
                and type_.__origin__ is tuple)
    else:
        # 3.6 and earlier
        # GenericMeta cannot be imported from typing, because it doesn't
        # exist in all versions, and it will fail the type check in those
        # versions as well, so we ignore it.
        return (isinstance(type_, typing.GenericMeta)
                and type_.__origin__ is typing.Tuple)
