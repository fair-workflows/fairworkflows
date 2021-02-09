from urllib.parse import urldefrag

import rdflib


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
