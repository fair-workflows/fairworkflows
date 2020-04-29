import rdflib
import requests
import xml.etree.ElementTree as et

from fairworkflows import FairData

class Nanopub:
    """
    Provides utility functions for searching, creating and publishing RDF graphs as assertions in a nanopublication.
    """

    NP = rdflib.Namespace("http://www.nanopub.org/nschema#")
    PPLAN = rdflib.Namespace("http://purl.org/net/p-plan#")
    PROV = rdflib.Namespace("http://www.w3.org/ns/prov#")
    DUL = rdflib.Namespace("http://ontologydesignpatterns.org/wiki/Ontology:DOLCE+DnS_Ultralite/")
    BPMN = rdflib.Namespace("https://www.omg.org/spec/BPMN/")
    PWO = rdflib.Namespace("http://purl.org/spar/pwo/")

    @staticmethod
    def search(searchtext, max_num_results=1000, apiurl='http://grlc.nanopubs.lod.labs.vu.nl//api/local/local/find_nanopubs_with_text'):
        """
        Searches the nanopub servers (at the specified grlc API) for any nanopubs matching the given search text,
        up to max_num_results.
        """

        if len(searchtext) == 0:
            return []

        # Query the nanopub server for the specified text
        searchparams = {'text': searchtext, 'graphpred': '', 'month': '', 'day': '', 'year': ''}
        r = requests.get(apiurl, params=searchparams)

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


    @staticmethod
    def fetch(uri, format='trig'):
        """
        Download the nanopublication at the specified URI (in trig format). Returns a FairData object.
        """

        extension = ''
        if format == 'trig':
            extension = '.trig'
        else:
            raise ValueError(f'Format not supported: {format}')

        r = requests.get(uri + extension)
        return FairData(data=r.text, source_uri=uri)


    @staticmethod
    def rdf(assertionrdf, uri='http://purl.org/nanopub/temp/mynanopub'):
        """
        Return the nanopub rdf, with given assertion and URI, but does not sign or publish.
        """

        this_np = rdflib.Namespace(uri+'#')

        # Set up different contexts
        np_rdf = rdflib.ConjunctiveGraph()
        head = rdflib.Graph(np_rdf.store, this_np.Head)
        assertion = rdflib.Graph(np_rdf.store, this_np.assertion)
        provenance = rdflib.Graph(np_rdf.store, this_np.provenance)
        pubInfo = rdflib.Graph(np_rdf.store, this_np.pubInfo)

        np_rdf.bind("", this_np)
        np_rdf.bind("np", NP)
        np_rdf.bind("p-plan", PPLAN)
        np_rdf.bind("prov", PROV)
        np_rdf.bind("dul", DUL)
        np_rdf.bind("bpmn", BPMN)
        np_rdf.bind("pwo", PWO)

        head.add((this_np[''], RDF.type, NP.Nanopublication))
        head.add((this_np[''], NP.hasAssertion, this_np.assertion))
        head.add((this_np[''], NP.hasProvenance, this_np.provenance))
        head.add((this_np[''], NP.hasPublicationInfo, this_np.pubInfo))

        assertion += assertionrdf

        creationtime = rdflib.Literal(datetime.now(),datatype=XSD.dateTime)
        provenance.add((this_np.assertion, PROV.generatedAtTime, creationtime))
        provenance.add((this_np.assertion, PROV.wasDerivedFrom, this_np.experiment))
        provenance.add((this_np.assertion, PROV.wasAttributedTo, this_np.experimentScientist))

        pubInfo.add((this_np[''], PROV.wasAttributedTo, this_np.DrBob))
        pubInfo.add((this_np[''], PROV.generatedAtTime, creationtime))

        return np_rdf


    @staticmethod
    def publish(assertionrdf, uri=None):
        """
        Publish the given assertion as a nanopublication with the given URI.
        Uses np commandline tool to sign and publish.
        """

        np_rdf = Nanopub.rdf(assertionrdf, uri=uri)

        # Create a temporary dir for files created during serializing and signing
        tempdir = tempfile.mkdtemp()

        # Convert nanopub rdf to trig
        fname = 'temp.trig'
        unsigned_fname = os.path.join(tempdir, fname)
        serialized = np_rdf.serialize(destination=unsigned_fname, format='trig')

        # Sign the nanopub and publish it
        signed_file = wrapper.sign(unsigned_fname)
        nanopuburl = wrapper.publish(signed_file)

        print(f'Published to {nanopuburl}')
        return nanopuburl

