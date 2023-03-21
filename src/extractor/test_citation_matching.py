import configparser
import functools
import configparser
from datasketch import MinHash, MinHashLSH
from elasticsearch import Elasticsearch
from extractor.python_wrapper import utils, wrappers
from ingestion.csx_extractor import CSXExtractorImpl
import re
import time
import pickle

def findMatchingDocumentsLSH(papers, miss_cat_count, match_index):
    config = configparser.ConfigParser()
    try:
        config.read("/pdfmef-code/src/extractor/python_wrapper/properties.config")
    except Exception as ex:
        print(ex)
    elasticConnectionProps = dict(config.items('ElasticConnectionProperties'))
    wrapper = wrappers.ElasticSearchWrapper(elasticConnectionProps)
    import re
    FP = 0
    FN = 0
    TP = 0
    TN = 0
    for paper in papers:
        miss = False
        try:
            if (True):
                title = paper['_source']['processed_title']
                #title = re.sub(r"[^a-zA-Z0-9 ]", " ", title)
                # elastic query + lsh
                if (match_index == 0):
                    documents = wrapper.get_batch_for_lsh_matching(title)
                # lsh only
                elif (match_index == 1):
                    documents = wrapper.get_all_doc_batch()
                # elastic query only
                else:
                    documents = wrapper.get_batch_for_elastic_query_match_only(title)


                if match_index == 2:
                    expected_result = paper['_source']['cat']
                    actual_result = paper['_source']['labelled_duplicates']
                    result = []
                    for doc in documents:
                        result.append(doc['_source']['core_id'])

                    actual_result_set = set(actual_result)
                    result_set = set(result)

                    if len(actual_result) == 0 and len(result) == 0:
                        TN += 1
                    elif len(actual_result) == 0 and len(result) == 1:
                        if (result[0] == paper['_source']['core_id']):
                            TN += 1
                        else:
                            FP += 1
                    elif actual_result_set.issubset(result_set):
                        TP += 1
                    elif len(actual_result) > 0 and len(result) == 0:
                        FN += 1
                    elif len(actual_result) > 0 and len(result) == 1 and result[0] == paper['_source']['core_id']:
                        FN += 1
                    else:
                        FP += 1

                else:

                    from pathlib import Path
                    my_file = Path("data")
                    if my_file.is_file() and match_index == 1:
                        rfile = open("data", "rb")
                        lsh = pickle.load(rfile)
                    else:
                        lsh = MinHashLSH(threshold=0.5, num_perm=128)

                        #print("here in training")
                        for doc in documents:
                            try:
                                title = doc['_source']['processed_title']
                                #print(title)
                                #title = re.sub(r"[^a-zA-Z0-9 ]", " ", title)
                                #title = re.sub(r'\s+', ' ', title)
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

                        if  match_index == 1:
                            data = pickle.dumps(lsh)
                            dfile = open("data", "wb")
                            dfile.write(data)

                    Title = paper['_source']['processed_title']
                    actual_result = paper['_source']['labelled_duplicates']
                    s = CSXExtractorImpl().create_shingles(Title, 5)
                    min_hash = MinHash(num_perm=128)
                    for shingle in s:
                        min_hash.update(shingle.encode('utf8'))
                    result = lsh.query(min_hash)
                    expected_result = paper['_source']['cat']

                    #print(result)

                    actual_result_set = set(actual_result)
                    result_set = set(result)

                    if len(actual_result) == 0 and len(result) == 0:
                        TN += 1
                    elif len(actual_result) == 0 and len(result) == 1:
                        if (result[0] == paper['_source']['core_id']):
                            TN += 1
                        else:
                            FP += 1
                    elif actual_result_set.issubset(result_set):
                        TP += 1
                    elif len(actual_result) > 0 and len(result) == 0:
                        FN += 1
                    elif len(actual_result) > 0 and len(result) == 1 and result[0] == paper['_source']['core_id']:
                        FN += 1
                    else:
                        FP += 1

        except Exception as es:
            print("exception in findMatchingDocumentsLSH with error msg: ", es)
    print("For type ---> \n", match_index)
    print("False positive -->  \n",FP)
    print("True positive --> \n",TP)
    print("False Negative --> \n",FN)
    print("true Negative --> \n",TN)

if __name__ == "__main__":
    es = Elasticsearch([{'host': '130.203.139.160', 'port': 9200}])
    mismatch_count = 0

    miss_cat_count = {"exact_dup": 0, "near_exact_dup": 0, "non_dup": 0}
    cat_count = {"exact_dup": 0, "near_exact_dup": 0, "non_dup": 0}
    res = es.search(index="dedupe_test", body = {
    "from": 0,
    'size' : 100000,
    'query': {
         "match_all": {
         }
    }
    })
    #print(res)
    dupe_ids = []
    all_docs = []
    docs = []
    for doc in res['hits']['hits']:
        id = doc['_source']['core_id']
        if (id in dupe_ids):
            pass
        else:
            all_docs.append(doc)
            dupe_id = doc['_source']['labelled_duplicates']
            dupe_ids.extend(dupe_id)


    docs = []
    for doc in all_docs:
        if doc['_source']['cat'] == 'near_exact_dup':
            if len(docs) == 10000:
                break

            docs.append(doc)
    '''
    for doc in all_docs:
        if doc['_source']['cat'] == 'non_dup':
            if len(docs) == 10000:
                break
            docs.append(doc)
    '''

    import random
    #all_docs = docs
    random.shuffle(docs)
    #docs = all_docs[:30000]
    #print(cat_count)
    print(len(docs))

    for i in [2]:
        start_time = time.time()
        findMatchingDocumentsLSH(docs, miss_cat_count, i)
        print("total time taken seconds ---> ", (time.time() - start_time))
        #print('miss classified documents for match type-> ', index, '\n', miss_cat_count)
