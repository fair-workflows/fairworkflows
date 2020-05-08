import ipywidgets as widgets
from ipywidgets import interact
from traitlets import Unicode, validate
from IPython.display import display, HTML
import tabulate

from fairworkflows import Nanopub, Workflowhub

def search():
    """
    Real-time searches for published data, with interactive ipywidget interface.
    Outputs results as an HTML table.
    """

    # Provide interactive search
    @interact(source=['nanopub', 'workflowhub', 'FAIR Data Point'], text='')
    def interactive_search(source='', text=''):

        if source == 'nanopub':
            # Search for up to 3 nanopubs
            results = Nanopub.search(text, max_num_results=3)
            table = [[r['v'], r['np'], r['date']] for r in results]

        elif source == 'workflowhub':
            # Search for up to 5 CWL workflows on the workflow hub
            results = Workflowhub.search(text, max_num_results=5)
            table = [[r['title'], r['url']] for r in results]

        # Output as table
        display(HTML(tabulate.tabulate(table, tablefmt='html')))

