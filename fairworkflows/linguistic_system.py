import sys
import warnings
from typing import List
import rdflib
from rdflib import DC, RDF, RDFS, OWL
from .namespaces import SCHEMAORG

class LinguisticSystem:
    def __init__(self, lstype: rdflib.URIRef = None, label: str = None, see_also: rdflib.URIRef = None, version_info: str = None):
        self.lstype = rdflib.URIRef(lstype)
        self.label = rdflib.Literal(label)
        self.see_also = rdflib.URIRef(see_also)
        self.version_info = rdflib.Literal(version_info)

    @classmethod
    def from_rdf(cls, rdf):
        lstype = _check_unique(list(rdf.objects(None, RDF.type)))
        label = _check_unique(list(rdf.objects(None, RDFS.label)))
        see_also = _check_unique(list(rdf.objects(None, RDFS.seeAlso)))
        version_info = _check_unique(list(rdf.objects(None, OWL.versionInfo)))
        return cls(lstype = lstype,
                   label=label,
                   see_also=see_also,
                   version_info=version_info)

    def generate_rdf(self, ref: rdflib.BNode):
        rdf = rdflib.Graph()
        if self.lstype:
            rdf.add( (ref, RDF.type, self.lstype) )
        if self.label:
            rdf.add( (ref, RDFS.label, self.label) )
        if self.see_also:
            rdf.add( (ref, RDFS.seeAlso, self.see_also) )
        if self.version_info:
            rdf.add( (ref, OWL.versionInfo, self.version_info) )
        return rdf

    def __str__(self):
        return (f'LinguisticSystem with type={self.lstype}, label={self.label}, '
                f'seeAlso={self.see_also}, versionInfo={self.version_info}')


def _check_unique(l: List):
    if len(l) == 0:
        return None
    if len(l) > 1:
        warnings.warn(f'Only one triple expected, but found {len(l)}: {l}')
    return l[0]



LINGSYS_ENGLISH = LinguisticSystem(lstype=DC.LinguisticSystem,
                                   label='en',
                                   see_also="http://www.datypic.com/sc/xsd/t-xsd_language.html")

LINGSYS_PYTHON = LinguisticSystem(lstype=SCHEMAORG.ComputerLanguage,
                                  label='python',
                                  version_info='.'.join([str(v) for v in sys.version_info]),
                                  see_also="https://www.wikidata.org/wiki/Q28865")

