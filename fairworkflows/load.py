import ipywidgets as widgets
from traitlets import Unicode, validate
from IPython.display import display

from ipyfilechooser import FileChooser

class Load(widgets.DOMWidget):

    def __init__(self):
        fc = FileChooser('/')
        display(fc)

        def change_title(chooser):
            chooser.title = '<b>Chosen</b>'

        fc.register_callback(change_title)
