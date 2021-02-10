import sys
import warnings
from typing import List
import rdflib
from rdflib import DC, RDF, RDFS, OWL
from .namespaces import SCHEMAORG

class LinguisticSystem:
    def __init__(self, lstype: rdflib.URIRef = None, label: str = None, seeAlso: rdflib.URIRef = None, versionInfo: str = None):
        self.lstype = rdflib.URIRef(lstype)
        self.label = rdflib.Literal(label)
        self.seeAlso = rdflib.URIRef(seeAlso)
        self.versionInfo = rdflib.Literal(versionInfo)

    @classmethod
    def from_rdf(cls, rdf):
        lstype = _check_unique(list(rdf.objects(None, RDF.type)))
        label = _check_unique(list(rdf.objects(None, RDFS.label)))
        seeAlso = _check_unique(list(rdf.objects(None, RDFS.seeAlso)))
        versionInfo = _check_unique(list(rdf.objects(None, OWL.versionInfo)))
        return cls(lstype = lstype,
                   label=label,
                   seeAlso=seeAlso,
                   versionInfo=versionInfo)

    def generate_rdf(self, ref: rdflib.BNode):
        rdf = rdflib.Graph()
        if self.lstype:
            rdf.add( (ref, RDF.type, self.lstype) )
        if self.label:
            rdf.add( (ref, RDFS.label, self.label) )
        if self.seeAlso:
            rdf.add( (ref, RDFS.seeAlso, self.seeAlso) )
        if self.versionInfo:
            rdf.add( (ref, OWL.versionInfo, self.versionInfo) )
        return rdf

LINGSYS_ENGLISH = LinguisticSystem(lstype=DC.LinguisticSystem,
                                   label='en',
                                   seeAlso="http://www.datypic.com/sc/xsd/t-xsd_language.html")

LINGSYS_PYTHON = LinguisticSystem(lstype=SCHEMAORG.ComputerLanguage,
                                  label='python',
                                  versionInfo='.'.join([str(v) for v in sys.version_info]),
                                  seeAlso="https://en.wikipedia.org/wiki/Python_(programming_language)")

def _check_unique(l: List):
    if len(l) == 0:
        return None
    if len(l) > 1:
        warnings.warn(f'Only one triple expected, but found {len(l)}: {l}')
    return l[0]
