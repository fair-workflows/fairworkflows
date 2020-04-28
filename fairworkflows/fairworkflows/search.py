import ipywidgets as widgets
from traitlets import Unicode, validate
from IPython.display import display
import requests
import xml.etree.ElementTree as et

class Search(widgets.DOMWidget):

    def __init__(self, server='http://server.nanopubs.lod.labs.vu.nl/'):

        layout=widgets.Layout(width='50%')

        searchtext = widgets.Text(
            value='',
            placeholder='Type search text',
            description='Nanosearch:',
            disabled=False,
            layout=layout
        )

        resultsbox = widgets.Select(
            options=[],
            value=None,
            description='',
            num_rows=5,
            disabled=False,
            layout=layout
        )

        def search(text_state):
            # Find (up to) 5 nanopubs matching the search text
            results = Search.nanopubs(text_state['new'], max_num_results=5) 

            # Display results in the Select UI element
            options = (r['v'] for r in results)
            resultsbox.options = options

        searchtext.observe(search, names='value')


#        searchtext.on_submit(search)
        display(searchtext, resultsbox)


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


