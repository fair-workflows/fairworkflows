import warnings

import rdflib


class RdfWrapper:
    def __init__(self, uri):
        self._rdf = rdflib.Graph()
        self._uri = uri
        self.self_ref = rdflib.URIRef(self._uri)

    @property
    def rdf(self) -> rdflib.Graph:
        """Get the rdf graph."""
        return self._rdf

    @property
    def uri(self) -> str:
        """Get the URI for this RDF."""
        return self._uri

    def get_attribute(self, predicate, always_return_list=False):
        """Get attribute.

        Get attribute of this RDF.

        Returns:
            The object for which the predicate corresponds to predicate
            argument and subject corresponds to this RDF itself. Return None
            if no attributes are found, or a list of attributes if multiple
            matching objects are found.
        """
        objects = list(self._rdf.objects(subject=self.self_ref,
                                         predicate=predicate))
        if always_return_list:
            return objects

        if len(objects) == 0:
            return None
        elif len(objects) == 1:
            return objects[0]
        else:
            return objects

    def set_attribute(self, predicate, value, overwrite=True):
        """Set attribute.

        Set attribute of this RDF. I.e. for the given `predicate` argument, set
        the object to the given `value` argument for the subject
        corresponding to this RDF. Optionally overwrite the attribute if it
        already exists (but throw a warning).
        """
        if overwrite and self.get_attribute(predicate) is not None:
            warnings.warn(f'A predicate {predicate} was already defined'
                          f'overwriting {predicate} for {self.self_ref}')
            self._rdf.remove((self.self_ref, predicate, None))
        self._rdf.add((self.self_ref, predicate, value))
