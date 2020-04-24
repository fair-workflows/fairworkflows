import ipywidgets as widgets
from traitlets import Unicode, validate
from IPython.display import display

class Search(widgets.DOMWidget):

    def __init__(self):
        searchtext = widgets.Text(
            value='',
            placeholder='Type something',
            description='Search:',
            disabled=False
        )

        resultsbox = widgets.Select(
            options=[],
            value=None,
            description='Results:',
            disabled=False
        )

        searchtext.on_submit(Search.search)
        display(searchtext, resultsbox)


    @staticmethod
    def search(sender):
        print("Searched for", sender.value)

