import configparser
import functools
import configparser
from datasketch import MinHash, MinHashLSH
from elasticsearch import Elasticsearch
from extractor.python_wrapper import utils, wrappers
from ingestion.csx_extractor import CSXExtractorImpl

def get_batch_for_lsh_matching(self, title):
    """Purpose: retrieves batch of documents to process from server"""

    body = ""
    try:
        body = {
                    "query":{
                      "bool":{
                         "should":
                            {
                               "match":{
                                  "title":{
                                     "query": title,
                                     "minimum_should_match":"85%"
                                  }
                               }
                            }
                      }
                    }
               }
    except Exception:
        pass
    print(body)
    results = self.get_connection_prod().search(index=settings.CLUSTERS_INDEX, body=body)
    self.s2_batch = results['hits']['hits']
    return self.s2_batch

def findMatchingDocumentsLSH(self, papers):
    config = configparser.ConfigParser()
    mismatch_count = 0
    try:
        config.read("/pdfmef-code/src/extractor/python_wrapper/properties.config")
    except Exception as ex:
        print(ex)
    elasticConnectionProps = dict(config.items('ElasticConnectionProperties'))
    wrapper = wrappers.ElasticSearchWrapper(elasticConnectionProps)
    for paper in papers:
        try:
            if (True):
                documents = wrapper.get_batch_for_lsh_matching(paper['_source']['original_title'])
                lsh = MinHashLSH(threshold=0.90, num_perm=128)
                for doc in documents:
                    try:
                        title = doc['_source']['original_title']
                        id = doc['_source']['core_id']
                        d={}
                        with_wildcard = False
                        count = 0
                        s = CSXExtractorImpl().create_shingles(title, 5)
                        min_hash = MinHash(num_perm=128)
                        for shingle in s:
                            min_hash.update(shingle.encode('utf8'))
                        if (not id in lsh):
                            lsh.insert(f"{id}", min_hash)
                    except Exception:
                        pass

                Title = paper['_source']['original_title']
                s = CSXExtractorImpl().create_shingles(Title, 5)
                min_hash = MinHash(num_perm=128)
                for shingle in s:
                    min_hash.update(shingle.encode('utf8'))
                result = lsh.query(min_hash)
                expected_result = paper['_source']['cat']
                if (result <=1 and expected_result != "non_dup"):
                    mismatch_count += 1
                if (result!=None):
                    if len(result) >= 1 and expected_result != "non_dup":
                        expected_match_id = paper['_source']['labelled_duplicates']
                        if expected_match_id not in result:
                            mismatch_count += 1
                    else:
                        mismatch_count += 1

        except Exception as es:
            print("exception in findMatchingDocumentsLSH with error msg: ", es)
    return mismatch_count

if __name__ == "__main__":
    es = Elasticsearch([{'host': '130.203.139.160', 'port': 9200}])
    res = es.search(index="dedupe_test", body = {
    'size' : 1000,
    'query': {
        'match_all' : {}
    }
    })
    print(res)
    print("%d documents found" % res['hits']['total'])
    data = [doc for doc in res['hits']['hits']]
    mismatch_count = findMatchingDocumentsLSH(data)
    print('miss classified documents --->', mismatch_count)
