
class FairData:
    """
    Stores the data fetched from FAIR datapoints, nanopub servers etc.
    """

    def __init__(self, data=None, source_uri=None):
        self.data = data
        self.source_uri = source_uri

    def __str__(self):
        s = f'Source URI = {self.source_uri}\n{self.data}'
        return s
