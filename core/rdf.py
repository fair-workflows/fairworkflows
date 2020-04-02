import rdflib
from rdflib.namespace import RDF, RDFS, DC, XSD, OWL

PPLAN = rdflib.Namespace("http://purl.org/net/p-plan/")
# TODO: Fix plex URL
PLEX = rdflib.Namespace("https://plex.org/")
EDAM = rdflib.Namespace("http://edamontology.org/")
PROV = rdflib.Namespace("http://www.w3.org/ns/prov/")
DUL = rdflib.Namespace("http://ontologydesignpatterns.org/wiki/Ontology:DOLCE+DnS_Ultralite/")
BPMN = rdflib.Namespace("https://www.omg.org/spec/BPMN/")
PWO = rdflib.Namespace("http://purl.org/spar/pwo/")
RDFG = rdflib.Namespace("http://www.w3.org/2004/03/trix/rdfg-1/")
NP = rdflib.Namespace("http://www.nanopub.org/nschema#")


def _create_workflow_rdf():
    # Create an rdf graph to add workflow metadata to.
    rdf = rdflib.Graph()
    # Bind all non-standard prefixes in use
    rdf.bind("p-plan", PPLAN)
    rdf.bind("plex", PLEX)
    rdf.bind("edam", EDAM)
    rdf.bind("prov", PROV)
    rdf.bind("dul", DUL)
    rdf.bind("bpmn", BPMN)
    rdf.bind("pwo", PWO)
    rdf.bind("rdfg", RDFG)
    rdf.bind("np", NP)

    return rdf


def _create_step(plex_workflow, name, description):
    # Autogenerate rdf metadata for this step
    rdf = rdflib.Graph()

    this_step = PLEX[name]

    rdf.add((this_step, RDF.type, PPLAN.Step))
    rdf.add((this_step, RDF.type, BPMN.scriptTask))
    rdf.add((this_step, PPLAN.isStepOfPlan, plex_workflow))

    # TODO: Define input and output

    rdf.add((this_step, DC.description, rdflib.Literal(description)))

    return rdf


class PlexWorkflow:

    def __init__(self, name):
        self.root_rdf = _create_workflow_rdf()
        self.plex_workflow = PLEX[name]

    def add_step(self, name, description):
        step = _create_step(self.plex_workflow, name, description)
        self.root_rdf += step

    def render(self, destination: str, format: str = 'turtle') -> None:
        self.root_rdf.serialize(destination, format)
