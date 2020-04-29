import requests
from html.parser import HTMLParser

from fairworkflows import FairData


class Workflowhub:
    """
    Search and fetch workflows from the EOSC-life workflow hub
    """

    @staticmethod
    def search(searchtext, max_num_results=1000, apiurl='https://dev.workflowhub.eu/workflows'):
        """
        Searches the EOSC-life workflowhub servers (at the specified API) for any CWL workflows
        matching the given search text, up to max_num_results.
        """

        ## WARNING: The following is a very quick and dirty solution to grab results from workflow hub
        ## straight from the HTML. This should be replaced with a proper search API as soon as available.

        if len(searchtext) == 0:
            return []

        # Query the nanopub server for the specified text
        searchparams = {'filter[query]': searchtext, 'filter[workflow_type]': 'CWL'}
        r = requests.get(apiurl, params=searchparams)

        # Parse the HTML directly to extract the workflow name and download URL
        # This is horrible and needs to be replaced when a real search endpoint is made available.
        extract = []
        class ParseWorkflowhubHTML(HTMLParser):

            def handle_starttag(self, tag, attrs):
                if tag == 'a':
                    for attr in attrs:
                        if attr[0] == 'href':
                            url = attr[1]
                            if 'workflows/' in url and 'download' in url:
                                extract.append(('url', url))
            def handle_endtag(self, tag):
                pass

            def handle_data(self, data):
                if len(data.strip()) > 0:
                    extract.append(('data', data))
                pass

        parser = ParseWorkflowhubHTML()
        parser.feed(r.text)
        
        rocrates = []
        last_data = ''
        description = ''
        for entry, data in extract:
            if last_data == 'Close':
                description = data
            last_data = data

            if entry == 'url':
                rocrates.append({'description': description, 'url': data})

            if len(rocrates) >= max_num_results:
                break

        return rocrates


    @staticmethod
    def fetch(uri):
        """
        Download the RO-Crate found at the specified URI. Returns a FairData object.
        """

        r = requests.get(uri)
        return FairData(data=r.text, source_uri=uri)
