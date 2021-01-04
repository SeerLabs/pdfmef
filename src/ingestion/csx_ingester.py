import time
from multiprocessing import Pool
import concurrent.futures as cf

from pathlib import Path
import os, time
import configparser

from ingestion.csx_clusterer import KeyMatcherClusterer
from ingestion.csx_extractor import CSXExtractorImpl
from ingestion.interfaces import CSXIngester
from models.elastic_models import Cluster, KeyMap
from services.elastic_service import ElasticService
from shutil import copyfile

def move_to_repository(filepath: str, docPath: str):
    tei_filename = str(filepath[str(filepath).rfind('/')+1:])
    paper_id = tei_filename[:tei_filename.rfind('.')]
    chunks = [paper_id[i:i + 2] for i in range(0, len(paper_id), 2)]
    filename = paper_id + ".pdf"
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), 'python_wrapper', 'properties.config'))
    pdf_repo_path = os.path.join("/data/repo/", chunks[0], chunks[1], chunks[2], chunks[3], chunks[4], chunks[5], chunks[6], paper_id, filename)
    os.makedirs(os.path.dirname(pdf_repo_path), exist_ok=True)
    copyfile(src=docPath, dst=pdf_repo_path)

def ingest_paper_parallel_func(combo):
    papers = CSXExtractorImpl().extract_textual_data(combo[0])
    move_to_repository(combo[0], combo[1])
    KeyMatcherClusterer().cluster_papers(papers)

class CSXIngesterImpl(CSXIngester):
    def __init__(self):
        self.extractor = CSXExtractorImpl()
        self.clusterer = KeyMatcherClusterer()
        self.elastic_service = ElasticService()

    def ingest_batch_parallel(self, teiDirectoryPath):
        start_time = time.time()
        pool = Pool()
        pool.map(ingest_paper_parallel_func, iter(Path(teiDirectoryPath).rglob("*.[tT][eE][iI]")))
        pool.close()
        pool.join()
        print("--- %s seconds ---" % (time.time() - start_time))

    def ingest_batch_parallel_files(self, fileList, documentPaths):
        print(" ------- Starting Ingestion -------")
        start_time = time.time()
        with cf.ThreadPoolExecutor(max_workers=1000) as executor:
            for idx in range(len(fileList)):
                executor.submit(ingest_paper_parallel_func, (fileList[idx], documentPaths[idx]))
        print("--- %s seconds ---" % (time.time() - start_time))


    def ingest_paper(self, filePath):
        papers = CSXExtractorImpl().extract_textual_data(filePath)
        KeyMatcherClusterer().cluster_papers(papers)

    def ingest_batch(self, dirpath):
        count = 0
        start_time = time.time()
        self.extractor.batch_extract_textual_data(dirpath)
        all_files = list(Path(dirpath).rglob("*.[tT][eE][iI]"))
        for filepath in all_files:
            count = count + 1
            if count % 20 == 0:
                print(count)
                print("--- %s seconds ---" % (time.time() - start_time))
            papers = self.extractor.extract_textual_data(filepath=str(filepath))
            self.clusterer.cluster_papers(papers)
        print("--- %s seconds ---" % (time.time() - start_time))


    def docs_generator(self, dirPath=None):
        count = 0
        all_files = list(Path(dirPath).rglob("*.[tT][eE][iI]"))
        for filepath in all_files:
            count = count + 1
            if count % 20 == 0:
                print(count)
            paper, citations = self.extractor.extract_textual_data(str(filepath))
            yield paper.to_dict(True)
            for citation in citations:
                yield citation.to_dict(True)

    def pdf_process_function(msg):
        print(" PDF processing")
        print(" [x] Received " + str(msg))

        time.sleep(5)  # delays for 5 seconds
        print(" PDF processing finished");
        return

    def pull_from_queue(self):
        pass

if __name__ == "__main__":
    csx_ingester = CSXIngesterImpl()
    Cluster.init(using=csx_ingester.elastic_service.get_connection())
    KeyMap.init(using=csx_ingester.elastic_service.get_connection())
    # KeyMap.init(using=csx_ingester.elastic_service.get_connection())
    # csx_ingester.ingest_batch_parallel("/data/sfk5555/ACL_results/2020072500")
