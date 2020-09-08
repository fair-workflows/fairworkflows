import warnings

import rdflib


class RdfWrapper:
    def __init__(self, uri):
        self._rdf = rdflib.Graph()
        self._uri = uri
        self.this = rdflib.URIRef(self._uri)

    def get_attribute(self, predicate):
        """Get attribute.

        Get attribute of this RDF.

        Returns:
            The object for which the predicate corresponds to predicate
            argument and subject corresponds to this RDF itself. Return None
            if no attributes are found, or a list of attributes if multiple
            matching objects are found.
        """
        objects = list(self._rdf.objects(subject=self.this,
                                         predicate=predicate))
        if len(objects) == 0:
            return None
        elif len(objects) == 1:
            return objects[0]
        else:
            return objects

    def set_attribute(self, predicate, value):
        """Set attribute.

        Set attribute of this RDF. I.e. for the given `predicate` argument, set
        the object to the given `value` argument for the subject
        corresponding to this RDF. If the attribute already exists overwrite
        it (but throw a warning).
        """
        if self.get_attribute(predicate) is not None:
            warnings.warn(f'A predicate {predicate} was already defined'
                          f'overwriting {predicate} for {self.this}')
            self._rdf.remove((self.this, predicate, None))
        self._rdf.add((self.this, predicate, value))
