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
                    if (len(documents) <=1 and expected_result != "non_dup"):
                        miss = True
                        FN += 1
                        #mismatch_count += 1
                    elif (documents!=None):
                        if len(documents) > 1 and expected_result != "non_dup":
                            expected_match_id = paper['_source']['labelled_duplicates']
                            core_id_list = []
                            for doc in documents:
                                core_id_list.append(doc['_source']['core_id'])
                            if expected_match_id[0] not in core_id_list:
                                miss = True
                                FP += 1
                            else:
                                TP += 1
                        elif len(documents) == 1 and expected_result == "non_dup":
                            TP += 1
                            pass
                        else:
                            FP += 1
                            miss = True

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
                    s = CSXExtractorImpl().create_shingles(Title, 5)
                    min_hash = MinHash(num_perm=128)
                    for shingle in s:
                        min_hash.update(shingle.encode('utf8'))
                    result = lsh.query(min_hash)
                    expected_result = paper['_source']['cat']
                    #print(result)
                    #print(paper)
                    #print('<---------------------------------------------------------->')
                    if (len(result) <=1 and expected_result != "non_dup"):
                        miss = True
                        FN += 1
                        #mismatch_count += 1
                    elif (result!=None):
                        if len(result) > 1 and expected_result != "non_dup":
                            expected_match_id = paper['_source']['labelled_duplicates']
                            if expected_match_id[0] not in result:
                                miss = True
                                FP += 1
                            else:
                                TP += 1
                        elif len(result) == 1 and expected_result == "non_dup":
                            TP += 1
                            pass
                        else:
                            FP += 1
                            miss = True
                #print(miss_cat_count["non_dup"])
                #cat = paper['_source']['cat']
                #miss_cat_count[cat] += 1 if (miss == True) else 0

        except Exception as es:
            print("exception in findMatchingDocumentsLSH with error msg: ", es)
    print("For type ---> \n", match_index)
    print("False positive -->  \n",FP)
    print("True positive --> \n",TP)
    print("False Negative --> \n",FN)

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



    print(len(all_docs))
    for doc in all_docs:
        print(doc['_source']['cat'])
        if (cat_count[doc['_source']['cat']] == 'near_exact_dup' or cat_count[doc['_source']['cat']] == 'non_dup'):
            docs.append(doc)
            cat_count[doc['_source']['cat']]+=1

    import random
    all_docs = docs
    random.shuffle(all_docs)
    docs = all_docs[:20000]
    #print(cat_count)
    print(len(docs))

    for i in [0, 2]:
        start_time = time.time()
        findMatchingDocumentsLSH(docs, miss_cat_count, i)
        print("total time taken seconds ---> ", (time.time() - start_time))
        #print('miss classified documents for match type-> ', index, '\n', miss_cat_count)
