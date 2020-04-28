import ipywidgets as widgets
from traitlets import Unicode, validate
from IPython.display import display
import requests
import xml.etree.ElementTree as et

class Search(widgets.DOMWidget):

    def __init__(self, server='http://server.nanopubs.lod.labs.vu.nl/'):

        searchtext = widgets.Text(
            value='',
            placeholder='Type something',
            description='Search:',
            disabled=False
        )

        resultsbox = widgets.Select(
            options=[],
            value=None,
            description='',
            disabled=False
        )

        def search(sender):
            results = Search.nanopubs(sender.value, max_num_results=3)                    
            resultsbox.options = tuple(results)
        
        searchtext.on_submit(search)
        display(searchtext, resultsbox)


    @staticmethod
    def nanopubs(searchtext, max_num_results=1000, apiurl='http://grlc.nanopubs.lod.labs.vu.nl//api/local/local/find_nanopubs_with_text'):
        """
        Searches the nanopub servers (at the specified grlc API) for any nanopubs matching the given search text,
        up to max_num_results.
        """

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


