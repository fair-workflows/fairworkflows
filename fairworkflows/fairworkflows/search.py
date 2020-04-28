import ipywidgets as widgets
from ipywidgets import interact
from traitlets import Unicode, validate
from IPython.display import display, HTML
import tabulate
import requests
import xml.etree.ElementTree as et

class Search(widgets.DOMWidget):

    def __init__(self):

        # Provide interactive search
        @interact(searchtext='', source=['nanopub', 'workflowhub', 'FAIR Data Point'])
        def interactive_search(searchtext, source='nanopub'):

            # Search for up to 3 nanopubs
            results = Search.nanopubs(searchtext, max_num_results=3)
  
            # Output as table
            table = [[r['v'], r['np'], r['date']] for r in results]
            display(HTML(tabulate.tabulate(table, tablefmt='html')))



    @staticmethod
    def nanopubs(searchtext, max_num_results=1000, apiurl='http://grlc.nanopubs.lod.labs.vu.nl//api/local/local/find_nanopubs_with_text'):
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


