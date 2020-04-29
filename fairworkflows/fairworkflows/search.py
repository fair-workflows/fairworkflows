import ipywidgets as widgets
from ipywidgets import interact, interactive, fixed
from traitlets import Unicode, validate
from IPython.display import display, HTML
import tabulate
import requests
import xml.etree.ElementTree as et

def search():

    # Provide interactive search
    @interact(source=['nanopub', 'workflowhub', 'FAIR Data Point'], text='')
    def interactive_search(source='', text=''):

        # Search for up to 3 nanopubs
        results = nanosearch(text, max_num_results=3)

        # Output as table
        table = [[r['v'], r['np'], r['date']] for r in results]
        display(HTML(tabulate.tabulate(table, tablefmt='html')))


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


class FairData:
    """
    Stores the data fetched from FAIR datapoints, nanopub servers etc.
    """

    def __init__(self, data=None, source_uri=None):
        self.data = data
        self.source_uri = source_uri

    def __str__(self):
        s = f'Source URI = {self.source_uri}\n{self.data}'
        return s
