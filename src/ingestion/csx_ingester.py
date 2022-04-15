import time
from multiprocessing import Pool
import concurrent.futures as cf

from pathlib import Path
import os, time
import configparser
from datasketch import MinHash, MinHashLSH

from ingestion.csx_clusterer import KeyMatcherClusterer
from ingestion.csx_extractor import CSXExtractorImpl
from ingestion.interfaces import CSXIngester
from models.elastic_models import Cluster, KeyMap, Cluster_original
from services.elastic_service import ElasticService
from shutil import copyfile

from elasticsearch import Elasticsearch
import settings

from settings import REPOSITORY_BASE_PATH

import logging

logger = logging.getLogger(__name__)


class Wrapper:

    #get_document_batch()
    #Purpose: retrieves batch of documents to process from server
    def get_document_batch(self):
        raise NotImplementedError('Extend me!')

    #get_document_ids()
    #
    #Purpose: parses the ids of all documents in a batch
    #Returns: list of string ids
    def get_document_ids(self):
        raise NotImplementedError('Extend me!')

    #get_document_paths()
    #
    #Purpose: parses the paths of all documents in a batch
    #Returns: list of document paths as strings
    def get_document_paths(self):
        raise NotImplementedError('Extend me!')

    #update_state(ids, state)
    #
    #Purpose: updates the extraction state of the given documents in the database
    #Parameters: ids - list of documents ids, state - the int state to assignt to each document
    def update_state(self, ids, state):
        raise NotImplementedError('Extend me!')

    #on_stop()
    #
    #Purpose: performs any necessary closing statements to free up connections and such
    def on_stop(self):
        raise NotImplementedError('Extend me!')


class ElasticSearchWrapper(Wrapper):
    def __init__(self, config):
        self.curr_index = 0
        self.file_path_sha1_mapping = {}
        self.file_path_source_url_map = {}
        self.batchSize = int(config['batchsize'])
        self.batch = None
        self.s2_batch = None


    def get_s2_doc_by_id(self, id):
        body = {
                 "query": {
                    "term": {
                      "id": {
                        "value": id
                      }
                    }
                  }
               }
        results = self.get_connection_prod().search(index=settings.S2_META_INDEX, body=body)
        return results['hits']['hits']

    def get_s2_batch_for_lsh_matching(self, author, year):
        """Purpose: retrieves batch of documents to process from server"""
        #print("inside get_s2_batch_for_lsh_matching---> \n")
        body = {
                 "from": 0,
                 "size": 10000,
                 "query": {
                   "bool": {
                     "must": [
                        {
                          "wildcard": {
                            "authors.name": author
                          }
                        },
                       {
                         "term": {
                           "year": year
                         }
                       }
                     ]
                   }
                 }
               }

        results = self.get_connection_prod().search(index=settings.S2_META_INDEX, body=body)
        #print("\n results\n")
        self.s2_batch = results['hits']['hits']
        return self.s2_batch

    def get_document_batch(self):
        """Purpose: retrieves batch of documents to process from server"""
        body = {
            "from": 0,
            "size": self.batchSize,
            "query": {
                "multi_match": {
                    "query": "fresh",
                    "fields": "text_status"
                }
            }
        }

        results = self.get_connection().search(index=settings.CRAWL_META_INDEX, body=body)
        self.batch = results['hits']['hits']

    def get_document_ids(self):
        """Purpose: parses the ids of all documents in a batch
            Returns: list of string ids"""
        ids = []
        for element in self.batch:
            ids.append(element['_id'])
        return ids

    def get_source_urls(self):
        urls = []
        for entry in self.batch:
            urls.append(entry['_source']['source'])
        return urls

    def get_connection(self):
        return Elasticsearch([{'host': '130.203.139.151', 'port': 9200}])

    def get_connection_prod(self):
        return Elasticsearch([{'host': '130.203.139.160', 'port': 9200}])

    def get_document_paths(self):
        """get_document_paths(docs)
        Purpose: parses the paths of all documents in a batch
        #Returns: list of document paths as strings"""
        paths = []
        for element in self.batch:
            strr = str(element['_source']['pdf_path'])
            if strr.endswith('\n'):
                strr = strr[:-1]
            paths.append(strr)
            self.file_path_sha1_mapping[strr] = element['_id']
            self.file_path_source_url_map[strr] = element['_source']['source']
        return paths

    def update_state(self, ids, state):
        """update_state(ids, state)
        Purpose: updates the extraction state of the given documents in the database
        Parameters: ids - list of documents ids, state - the int state to assignt to each document"""
        body = {
            "script": {
                "source": "ctx._source.text_status=" + "'" + state + "'",
                "lang": "painless"
            },
            "query": {
                "terms": {
                    "_id": ids
                }
            }
        }
        print(body['script'])
        try:
            status = self.get_connection().update_by_query(index=settings.CRAWL_META_INDEX, body=body,
                                                           request_timeout=1000, refresh=True)
        except Exception as e:
            print(e)

    def on_stop(self):
        """Purpose: perform necessary closing statements
         Behavior: nothing to do"""
        print('closed')

    def file_path_to_id(self, fileName):
        return self.file_path_sha1_mapping[fileName]

    def file_path_to_source_url(self, filePath):
        return self.file_path_source_url_map[filePath]

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

def create_shingles(doc, k):
    """
    Creates shingles and stores them in sets

    Paramaters
    ----------

    Returns
    -------
    """
    shingled_set = set() # create an empty set

    doc_length = len(doc)

    # iterate through the string and slice it up by k-chars at a time
    for idx in range(doc_length - k + 1):
        doc_slice = doc[idx:idx + k]
        shingled_set.add(doc_slice)

    return shingled_set

def findMatchingDocumentsS2orcLSH(papers):
    config = configparser.ConfigParser()
    config.read("/pdfmef-code/src/extractor/python_wrapper/properties.config")
    #print(config.items)
    elasticConnectionProps = dict(config.items('ElasticConnectionProperties'))
    wrapper = ElasticSearchWrapper(elasticConnectionProps)

    for paper in papers:
        try:
            if (paper.authors == None):
                continue
            if (paper.authors!=None and len(paper.authors) > 0 and paper.pub_info and paper.pub_info.year):
                print('incoming paper\n')
                print("*"+paper.authors[0]['surname']+"*")
                print(paper.pub_info['year'])
                print(paper.title)
                print('\n')
                documents = wrapper.get_s2_batch_for_lsh_matching("*"+paper.authors[0]['surname']+"*", paper.pub_info['year'])
                print(len(documents))
                lsh = MinHashLSH(threshold=0.5, num_perm=128)
                for doc in documents:
                    title = doc['_source']['title']
                    id = doc['_source']['id']

                    d={}
                    with_wildcard = False
                    count = 0

                    s = create_shingles(title, 5)

                    min_hash = MinHash(num_perm=128)
                    for shingle in s:
                        min_hash.update(shingle.encode('utf8'))

                    if (not id in lsh):
                        lsh.insert(f"{id}", min_hash)

                Title = paper.title
                s = create_shingles(Title, 5)
                min_hash = MinHash(num_perm=128)
                for shingle in s:
                    min_hash.update(shingle.encode('utf8'))
                result = lsh.query(min_hash)
                if (result == None):
                    continue
                if (result!=None):
                    print(result)
                    if len(result) > 0:
                        print("matching documents from the minhash\n")
                        print(result[0])
                        mergeMatchingDocs(wrapper, paper, result[0])

        except Exception as es:
            print("exception in findMatchingDocumentsS2orcLSH with error msg: ", es)

def mergeMatchingDocs(wrapper, paper, matching_s2org_doc_id):
    matching_s2org_doc = wrapper.get_s2_doc_by_id(matching_s2org_doc_id)
    for doc in matching_s2org_doc:
        paper.title = matching_s2org_doc['_source']['title']
        paper.pub_info.year = matching_s2org_doc['_source']['year']
        paper.authors = matching_s2org_doc['_source']['authors']
        print("merged document successfully with the document from s2org")

def ingest_paper_parallel_func(combo):
    papers = CSXExtractorImpl().extract_textual_data(combo[0], combo[2])
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
