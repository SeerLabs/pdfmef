import time
from multiprocessing import Pool
import concurrent.futures as cf

from pathlib import Path
import os, time
import configparser

from ingestion.csx_clusterer import KeyMatcherClusterer
from ingestion.csx_extractor import CSXExtractorImpl
from ingestion.interfaces import CSXIngester
from models.elastic_models import Cluster, KeyMap, Cluster_original
from services.elastic_service import ElasticService
from shutil import copyfile

from settings import REPOSITORY_BASE_PATH

import logging

logger = logging.getLogger(__name__)

def move_to_repository(filepath: str, docPath: str):
    try:
        tei_filename = str(filepath[str(filepath).rfind('/') + 1:])
        paper_id = tei_filename[:tei_filename.rfind('.')]
        chunks = [paper_id[i:i + 2] for i in range(0, len(paper_id), 2)]
        filename = paper_id + ".pdf"
        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'python_wrapper', 'properties.config'))
        pdf_repo_path = os.path.join(REPOSITORY_BASE_PATH, chunks[0], chunks[1], chunks[2], chunks[3], chunks[4], chunks[5],
                                    chunks[6], paper_id, filename)
        os.makedirs(os.path.dirname(pdf_repo_path), exist_ok=True)
        copyfile(src=docPath, dst=pdf_repo_path)
    except Exception as e:
        tei_filename = str(filepath[str(filepath).rfind('/') + 1:])
        paper_id = tei_filename[:tei_filename.rfind('.')]
        logger.error("exception while copying files to repo server for paper id: "+paper_id)
        print("exception while copying files to repo server: "+e)

def findMatchingDocumentsS2orcLSH(papers):
    print("inside findMatchingDocumentsS2orcLSH \n")
    config = configparser.ConfigParser()
    config.read("/pdfmef-code/src/extractor/python_wrapper/properties.config")
    elasticConnectionProps = dict(config.items('ElasticConnectionProperties'))
    wrapper = wrappers.ElasticSearchWrapper(elasticConnectionProps)
    print("\n paper --> \n")
    print(papers)

    for paper in papers:
        try:
            print("inside findMatchingDocumentsS2orcLSH incoming paper is ---> \n")
            print(paper)
            print("\n")
            if (paper.authors and paper.authors.size == 1 and paper.pub_info and year in paper.pub_info):
                documents = wrapper.get_s2_batch_for_lsh_matching(paper.authors[0].name, paper.pub_info.year)
                print("inside findMatchingDocumentsS2orcLSH s2orc documents is ---> \n")
                lsh = MinHashLSH(threshold=0.8, num_perm=128)
                for doc in documents:
                    print(doc)
                    print("\n")
                    if (not (year in doc and authors in doc)):
                        continue
                    title = doc['title']
                    id = doc['id']

                    print("inside findMatchingDocumentsS2orcLSH s2orc paper title is: ", title)

                    d={}
                    with_wildcard = False
                    count = 0

                    s = create_shingles(title, 5)

                    min_hash = MinHash(num_perm=128)
                    for shingle in s:
                        min_hash.update(shingle.encode('utf8'))

                    lsh.insert(f"{id}", min_hash)

                Title = paper.title

                print("inside findMatchingDocumentsS2orcLSH incoming paper title is: ", Title)

                s = create_shingles(Title, 5)
                min_hash = MinHash(num_perm=128)
                for shingle in s:
                    min_hash.update(shingle.encode('utf8'))
                result = lsh.query(res)
                if len(result) > 0:
                    mergeMatchingDocs(wrapper, paper, result[0])

        except Exception as es:
            print("exception in findMatchingDocumentsS2orcLSH with error msg: ", es)

def mergeMatchingDocs(wrapper, paper, matching_s2org_doc_id):
    matching_s2org_doc = wrapper.get_s2_doc_by_id(matching_s2org_doc_id)
    paper.title = matching_s2org_doc.title
    paper.pub_info.year = matching_s2org_doc.year
    paper.authors = matching_s2org_doc.authors

def ingest_paper_parallel_func(combo):
    papers = CSXExtractorImpl().extract_textual_data(combo[0], combo[2])
    print("inside ingest_paper_parallel_func--->")
    print(papers)
    findMatchingDocumentsS2orcLSH(papers)
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

    def ingest_batch_parallel_files(self, fileList, documentPaths, source_urls):
        print(" ------- Starting Ingestion -------")
        start_time = time.time()
        logger.info("------ starting batch parallel file ingestion for file size: "+ str(len(fileList)) + " start time: "+str(start_time))
        start_time = time.time()
        with cf.ThreadPoolExecutor(max_workers=1000) as executor:
            for idx in range(len(fileList)):
                executor.submit(ingest_paper_parallel_func, (fileList[idx], documentPaths[idx], source_urls[idx]))
        print("--- %s seconds ---" % (time.time() - start_time))
        logger.info("------ batch parallel file ingestion complete:  "+str(time.time() - start_time))

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
        print(" PDF processing finished")
        return

    def pull_from_queue(self):
        pass

if __name__ == "__main__":
    csx_ingester = CSXIngesterImpl()
    Cluster.init(using=csx_ingester.elastic_service.get_connection())
    KeyMap.init(using=csx_ingester.elastic_service.get_connection())
    # KeyMap.init(using=csx_ingester.elastic_service.get_connection())
    csx_ingester.ingest_batch_parallel("/pdfmef-code/extraction-results/results2021100100202110010020211008002021100800")
