import ipywidgets as widgets
from traitlets import Unicode, validate
from IPython.display import display

class Hello(widgets.DOMWidget):

    def __init__(self):
        def on_button_clicked(b):
            with self.output:
                print("Button clicked.")

        button = widgets.Button(description="Click Me!")
        self.output = widgets.Output()

        button.on_click(on_button_clicked)

        display(button, self.output)
