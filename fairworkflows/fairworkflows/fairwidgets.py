import ipywidgets as widgets
from ipywidgets import interact
from traitlets import Unicode, validate
from IPython.display import display, HTML
import tabulate

import fairworkflows as fair

def search():
    """
    Real-time searches for published data, with interactive ipywidget interface.
    Outputs results as an HTML table.
    """

    # Provide interactive search
    @interact(source=['nanopub', 'workflowhub', 'FAIR Data Point'], text='')
    def interactive_search(source='', text=''):

        # Search for up to 3 nanopubs
        results = fair.nanosearch(text, max_num_results=3)

        # Output as table
        table = [[r['v'], r['np'], r['date']] for r in results]
        display(HTML(tabulate.tabulate(table, tablefmt='html')))
