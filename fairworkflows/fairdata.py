
class FairData:
    """
    Stores the data fetched from FAIR datapoints, nanopub servers etc.
    """

    def __init__(self, data=None, source_uri=None):
        self._data = data
        self._source_uri = source_uri

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = data

    @property
    def source_uri(self):
        return self._source_uri

    @source_uri.setter
    def source_uri(self, source_uri):
        self._source_uri = source_uri

    def __str__(self):
        s = f'Source URI = {self._source_uri}\n{self._data}'
        return s
