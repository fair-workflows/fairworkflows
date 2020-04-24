import ipywidgets as widgets
from traitlets import Unicode, validate
from IPython.display import display
from SPARQLWrapper import SPARQLWrapper


class Step(widgets.DOMWidget):

    def __init__(self):
        tasktext = widgets.Text(
            value='',
            placeholder='Type something',
            description='Description:',
            disabled=False
        )

        print(tasktext)

        def make_step(sender):
            widgets.Output().clear_output()
            print(sender.value)
            tasktext.close()
            self.close()

        tasktext.on_submit(make_step)
        display(tasktext)

        print("done")


