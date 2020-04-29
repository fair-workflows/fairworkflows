import requests
import xml.etree.ElementTree as et

from fairworkflows import FairData

def nanosearch(searchtext, max_num_results=1000, apiurl='http://grlc.nanopubs.lod.labs.vu.nl//api/local/local/find_nanopubs_with_text'):
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


def nanofetch(uri, format='trig'):
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
