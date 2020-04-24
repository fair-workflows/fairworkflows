import ipywidgets as widgets
from traitlets import Unicode, validate
from IPython.display import display
from SPARQLWrapper import SPARQLWrapper



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

        searchtext.on_submit(Search.search)
        display(searchtext, resultsbox)


    @staticmethod
    def search(sender):
        print("Searched for", sender.value)
        
        queryString = "SELECT * WHERE { ?s ?p ?o. }"
        sparql = SPARQLWrapper('http://server.nanopubs.lod.labs.vu.nl/')

        sparql.setQuery(queryString)

        try :
           ret = sparql.query()
        except :
           print("Error when querying")

        print('Result:', ret)

