import io
import tempfile
from urllib.parse import urljoin, urlparse
from pathlib import Path

import requests

from . import ROCrate


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
        headers = {"Accept": "application/json"}
        r = requests.get(apiurl, headers=headers, params=searchparams)

        results = []
        for r in r.json()['data']:
            title = r['attributes']['title']
            url = urljoin(urljoin(apiurl, r['links']['self'] + '/'), "download")
            rocrate = {'title': title, 'url': url}
            results.append(rocrate)
            if len(results) >= max_num_results:
                break

        return results

    @staticmethod
    def fetch(uri):
        """
        Download the RO-Crate zip file found at the specified URI,
        and returns it as an ROCrate python object.
        """

        # TODO: Create cache for for RO crates
        # Fetch the RO-Crate .zip, and open it (in memory)
        r = requests.get(uri)

        temp_dir = Path(tempfile.mkdtemp())
        zip_path = temp_dir / 'ro-crate.zip'
        with open(zip_path, 'wb') as outfile:
            outfile.write(r.content)

        return ROCrate(zip_path)
