import requests
import zipfile
import io
from urllib.parse import urljoin

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
        headers={"Accept": "application/json"}
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
        Download the RO-Crate zip file found at the specified URI.
        Decompresses it, extracts the CWL file, and returns a FairData object.
        """

        # Fetch the RO-Crate .zip, and open it (in memory)
        r = requests.get(uri)

        # Find the first CWL file (for now)
        cwldata = None
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            for fname in z.namelist():
                if '.cwl' in fname:
                    cwldata = z.open(fname, 'r').read().decode('utf-8')
                    break

        return FairData(data=cwldata, source_uri=uri)
