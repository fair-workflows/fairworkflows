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
           
            # Current nanopubs server grlc api
            apiurl = "http://grlc.nanopubs.lod.labs.vu.nl//api/local/local/find_nanopubs_with_text"

            # Query the nanopub server for the specified text
            searchparams = {'text': sender.value, 'graphpred': '', 'month': '', 'day': '', 'year': ''}
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
                    
            resultsbox.options = tuple(nanopubs)

        searchtext.on_submit(search)
        display(searchtext, resultsbox)



