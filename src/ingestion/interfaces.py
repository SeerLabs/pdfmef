__author__ = "Sai Raghav Keesara"
__copyright__ = "Copyright 2020, Penn State University"
__license__ = ""
__version__ = "1.0"
__maintainer__ = "Sai Raghav Keesara"
__email__ = "sai@psu.edu"
__status__ = "Development"

from models.elastic_models import Cluster


class CSXExtractor:

    def __init__(self):
        pass

    def extract_textual_data(self, filepath: str):
        raise NotImplementedError('Extend me!')

    def batch_extract_textual_data(self, dirPath: str):
        raise NotImplementedError('Extend me!')

    def extract_figures(self, filepath: str):
        raise NotImplementedError('Extend me!')

    def batch_extract_figures(self, dirPath: str):
        raise NotImplementedError('Extend me!')

class CSXClusterer:

    def cluster_paper(self, paper: Cluster):
        raise NotImplementedError('Extend me!')

    def cluster_papers(self, paper: Cluster):
        raise NotImplementedError('Extend me!')

    def recluster_paper(self, paper: Cluster):
        raise NotImplementedError('Extend me!')

class CSXIngester:

    def ingest_paper(self, filepath: str):
        raise NotImplementedError('Extend me!')