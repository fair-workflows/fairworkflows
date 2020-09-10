import warnings

import rdflib


class RdfWrapper:
    def __init__(self, uri):
        self._rdf = rdflib.Graph()
        self._uri = uri
        self.self_ref = rdflib.term.BNode('FairObject')
        self._is_modified = False

    @property
    def rdf(self) -> rdflib.Graph:
        """Get the rdf graph."""
        return self._rdf

    @property
    def uri(self) -> str:
        """Get the URI for this RDF."""
        return self._uri

    @property
    def is_modified(self) -> bool:
        """Returns true if the RDF has been modified since initialisation"""
        return self._is_modified

    def get_attribute(self, predicate):
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
            warnings.warn(f'A predicate {predicate} was already defined\n'
                          f'Overwriting {predicate} for {self.self_ref}')
            self._rdf.remove((self.self_ref, predicate, None))
        self._rdf.add((self.self_ref, predicate, value))
        self._is_modified = True

    def anonymise_rdf(self):
        """
        Replace any subjects or objects referring directly to the rdf uri, with a blank node
        """
        for s, p, o in self._rdf:
            if self._uri == str(s):
                self._rdf.remove((s, p, o))
                self._rdf.add((self.self_ref, p, o))
            if self._uri == str(o):
                self._rdf.remove((s, p, o))
                self._rdf.add((s, p, self.self_ref))
