import os
import rdflib
from rdflib.namespace import RDF, RDFS, DC, DCTERMS, XSD, OWL
from datetime import datetime
import tempfile
import requests
import xml.etree.ElementTree as et
from pathlib import Path
from enum import Enum, unique
from urllib.parse import urldefrag

from fairworkflows import nanopub_wrapper


class Nanopub:
    """
    Provides utility functions for searching, creating and publishing RDF graphs as assertions in a nanopublication.
    """

    NP = rdflib.Namespace("http://www.nanopub.org/nschema#")
    NPX = rdflib.Namespace("http://purl.org/nanopub/x/")
    PPLAN = rdflib.Namespace("http://purl.org/net/p-plan#")
    PROV = rdflib.Namespace("http://www.w3.org/ns/prov#")
    DUL = rdflib.Namespace("http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#")
    BPMN = rdflib.Namespace("http://dkm.fbk.eu/index.php/BPMN2_Ontology#")
    PWO = rdflib.Namespace("http://purl.org/spar/pwo#")
    HYCL = rdflib.Namespace("http://purl.org/petapico/o/hycl#")

    AUTHOR = rdflib.Namespace("http://purl.org/person#")

    DEFAULT_URI = 'http://purl.org/nanopub/temp/mynanopub'

    @unique
    class Format(Enum):
        """
        Enums to specify the format of nanopub desired   
        """
        TRIG = 1


    class NanopubObj:
        """
        Stores the rdf parsed from nanopubs from the nanopub servers etc.
        """

        def __init__(self, rdf=None, source_uri=None):
            self._rdf = rdf
            self._source_uri = source_uri

        @property
        def rdf(self):
            return self._rdf

        @rdf.setter
        def rdf(self, rdf):
            self._rdf = rdf

        @property
        def source_uri(self):
            return self._source_uri

        @source_uri.setter
        def source_uri(self, source_uri):
            self._source_uri = source_uri

        def __str__(self):
            s = f'Source URI = {self._source_uri}\n'
            s += self._rdf.serialize(format='trig').decode('utf-8')
            return s


    @staticmethod
    def search_text(searchtext, max_num_results=1000, apiurl='http://grlc.nanopubs.lod.labs.vu.nl//api/local/local/find_nanopubs_with_text'):
        """
        Searches the nanopub servers (at the specified grlc API) for any nanopubs matching the given search text,
        up to max_num_results.
        """

        if len(searchtext) == 0:
            return []

        searchparams = {'text': searchtext, 'graphpred': '', 'month': '', 'day': '', 'year': ''}

        return Nanopub._search(searchparams=searchparams, max_num_results=max_num_results, apiurl=apiurl)


    @staticmethod
    def search_pattern(subj=None, pred=None, obj=None, max_num_results=1000, apiurl='http://grlc.nanopubs.lod.labs.vu.nl//api/local/local/find_nanopubs_with_pattern'):
        """
        Searches the nanopub servers (at the specified grlc API) for any nanopubs matching the given RDF pattern,
        up to max_num_results.
        """

        searchparams = {}
        if subj:
            searchparams['subj'] = subj
        if pred:
            searchparams['pred'] = pred
        if obj:
            searchparams['obj'] = obj

        return Nanopub._search(searchparams=searchparams, max_num_results=max_num_results, apiurl=apiurl)


    @staticmethod
    def search_things(thing_type=None, searchterm=' ', max_num_results=1000, apiurl='http://grlc.nanopubs.lod.labs.vu.nl/api/local/local/find_things'):
        """
        Searches the nanopub servers (at the specified grlc API) for any nanopubs of the given type, with given search term,
        up to max_num_results.
        """

        searchparams = {}
        if not thing_type or not searchterm:
            print(f"Received thing_type='{thing_type}', searchterm='{searchterm}'")
            raise ValueError('thing_type and searchterm must BOTH be specified in calls to Nanopub.search_things')

        searchparams['type'] = thing_type
        searchparams['searchterm'] = searchterm

        return Nanopub._search(searchparams=searchparams, max_num_results=max_num_results, apiurl=apiurl)


    @staticmethod
    def _search(searchparams=None, max_num_results=None, apiurl=None):
        """
        General nanopub server search method. User should use e.g. search_text() or search_pattern() instead.
        """

        if apiurl is None:
            raise ValueError('kwarg "apiurl" must be specified. Consider using search_text() function instead.')

        if max_num_results is None:
            raise ValueError('kwarg "max_num_results" must be specified. Consider using search_text() function instead.')

        if searchparams is None:
            raise ValueError('kwarg "searchparams" must be specified. Consider using search_text() function instead.')


        # Query the nanopub server for the specified text
#        headers = {"Accept": "application/json"}
#        r = requests.get(apiurl, params=searchparams, headers=headers)
        r = requests.get(apiurl, params=searchparams)

        print(r.url)
        print(r.text)

        # Check for success
        if r.ok:
            # Parse the resulting xml into a table
            xmltree = et.ElementTree(et.fromstring(r.text))
            xmlroot = xmltree.getroot()
            namespace = '{http://www.w3.org/2005/sparql-results#}'
            results = xmlroot.find(namespace + 'results')

            nanopubs = []
            for child in results:

                nanopub = {}
                for sub in child.iter(namespace + 'binding'):
                    nanopub[sub.get('name')] = sub[0].text
                nanopubs.append(nanopub)

                if len(nanopubs) >= max_num_results:
                    break

            return nanopubs
        else:
            return [{'Error': f'Error when searching {apiurl}: Status code {r.status_code}'}]

    @staticmethod
    def fetch(uri, format=Format.TRIG):
        """
        Download the nanopublication at the specified URI (in specified format). If successful, returns a Nanopub object.
        """

        extension = ''
        if format == Nanopub.Format.TRIG:
            extension = '.trig'
            parse_format = 'trig'
        else:
            raise ValueError(f'Format not supported: {format}')


        r = requests.get(uri + extension)
        r.raise_for_status()

        if r.ok:
            nanopub_rdf = rdflib.ConjunctiveGraph()
            nanopub_rdf.parse(data=r.text, format=parse_format)
            return Nanopub.NanopubObj(rdf=nanopub_rdf, source_uri=uri)


    @staticmethod
    def rdf(assertionrdf, uri=DEFAULT_URI, introduces_concept=None, derived_from=None):
        """
        Return the nanopub rdf, with given assertion and (defrag'd) URI, but does not sign or publish.
        """

        # Make sure passed URI is defrag'd        
        uri, _ = urldefrag(uri)

        this_np = rdflib.Namespace(uri+'#')

        # Set up different contexts
        np_rdf = rdflib.ConjunctiveGraph()
        head = rdflib.Graph(np_rdf.store, this_np.Head)
        assertion = rdflib.Graph(np_rdf.store, this_np.assertion)
        provenance = rdflib.Graph(np_rdf.store, this_np.provenance)
        pubInfo = rdflib.Graph(np_rdf.store, this_np.pubInfo)

        np_rdf.bind("", this_np)
        np_rdf.bind("np", Nanopub.NP)
        np_rdf.bind("npx", Nanopub.NPX)
        np_rdf.bind("p-plan", Nanopub.PPLAN)
        np_rdf.bind("prov", Nanopub.PROV)
        np_rdf.bind("dul", Nanopub.DUL)
        np_rdf.bind("bpmn", Nanopub.BPMN)
        np_rdf.bind("pwo", Nanopub.PWO)
        np_rdf.bind("hycl", Nanopub.HYCL)
        np_rdf.bind("dc", DC)
        np_rdf.bind("dcterms", DCTERMS)

        head.add((this_np[''], RDF.type, Nanopub.NP.Nanopublication))
        head.add((this_np[''], Nanopub.NP.hasAssertion, this_np.assertion))
        head.add((this_np[''], Nanopub.NP.hasProvenance, this_np.provenance))
        head.add((this_np[''], Nanopub.NP.hasPublicationInfo, this_np.pubInfo))

        assertion += assertionrdf

        creationtime = rdflib.Literal(datetime.now(),datatype=XSD.dateTime)
        provenance.add((this_np.assertion, Nanopub.PROV.generatedAtTime, creationtime))
        provenance.add((this_np.assertion, Nanopub.PROV.wasAttributedTo, this_np.experimentScientist))

        if derived_from:
            provenance.add((this_np.assertion, Nanopub.PROV.wasDerivedFrom, derived_from))

        pubInfo.add((this_np[''], Nanopub.PROV.wasAttributedTo, Nanopub.AUTHOR.DrBob))
        pubInfo.add((this_np[''], Nanopub.PROV.generatedAtTime, creationtime))

        if introduces_concept:
            pubInfo.add((this_np[''], Nanopub.NPX.introduces, introduces_concept))

        return np_rdf


    @staticmethod
    def publish(assertionrdf, uri=None, introduces_concept=None, derived_from=None):
        """
        Publish the given assertion as a nanopublication with the given URI.
        Uses np commandline tool to sign and publish.
        """

        if uri is None:
            np_rdf = Nanopub.rdf(assertionrdf, introduces_concept=introduces_concept, derived_from=derived_from)
        else:
            np_rdf = Nanopub.rdf(assertionrdf, uri=uri, introduces_concept=introduces_concept, derived_from=derived_from)

        # Create a temporary dir for files created during serializing and signing
        tempdir = tempfile.mkdtemp()

        # Convert nanopub rdf to trig
        fname = 'temp.trig'
        unsigned_fname = os.path.join(tempdir, fname)
        serialized = np_rdf.serialize(destination=unsigned_fname, format='trig')

        # Sign the nanopub and publish it
        signed_file = nanopub_wrapper.sign(unsigned_fname)
        nanopuburi = nanopub_wrapper.publish(signed_file)

        print(f'Published to {nanopuburi}')
        return nanopuburi


    @staticmethod
    def claim(text, rdftriple=None):
        """
        Publishes a claim, either as a plain text statement, or as an rdf triple (or both) 
        """
        assertionrdf = rdflib.Graph()

        assertionrdf.add((Nanopub.AUTHOR.DrBob, Nanopub.HYCL.claims, rdflib.Literal(text)))

        if rdftriple is not None:
            assertionrdf.add(rdftriple)

        Nanopub.publish(assertionrdf)
