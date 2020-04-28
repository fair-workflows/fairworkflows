import ipywidgets as widgets
from traitlets import Unicode, validate
from IPython.display import display
import requests

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
        print("Searching for", sender.value)
       
        apiurl = "http://grlc.nanopubs.lod.labs.vu.nl//api/local/local/find_nanopubs_with_text"
        searchparams = {'text': sender.value, 'graphpred': '', 'month': '', 'day': '', 'year': ''}
        r = requests.get(apiurl, params=searchparams)


        print('Result:', r.text)

