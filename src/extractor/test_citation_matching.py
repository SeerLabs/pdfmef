import configparser
import functools
import configparser
from datasketch import MinHash, MinHashLSH
from elasticsearch import Elasticsearch
from extractor.python_wrapper import utils, wrappers
from ingestion.csx_extractor import CSXExtractorImpl
import re

def findMatchingDocumentsLSH(papers, miss_cat_count):
    config = configparser.ConfigParser()
    try:
        config.read("/pdfmef-code/src/extractor/python_wrapper/properties.config")
    except Exception as ex:
        print(ex)
    elasticConnectionProps = dict(config.items('ElasticConnectionProperties'))
    wrapper = wrappers.ElasticSearchWrapper(elasticConnectionProps)
    import re
    for paper in papers:
        miss = False
        try:
            if (True):
                title = paper['_source']['processed_title']
                #title = re.sub(r"[^a-zA-Z0-9 ]", " ", title)
                documents = wrapper.get_batch_for_lsh_matching(title)
                lsh = MinHashLSH(threshold=0.6, num_perm=128)
                for doc in documents:
                    try:
                        title = doc['_source']['processed_title']
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

                Title = paper['_source']['processed_title']
                #Title = re.sub(r"[^a-zA-Z0-9 ]", " ", Title)
                #Title = re.sub(r'\s+', ' ', Title)
                s = CSXExtractorImpl().create_shingles(Title, 5)
                min_hash = MinHash(num_perm=128)
                for shingle in s:
                    min_hash.update(shingle.encode('utf8'))
                result = lsh.query(min_hash)
                expected_result = paper['_source']['cat']
                #print(paper)
                #print('<---------------------------------------------------------->')
                if (len(result) <=1 and expected_result != "non_dup"):
                    print(expected_result)
                    print(paper['_source']['labelled_duplicates'])
                    print(">>>>>>>>>>>>>>>>>>>>>>>>>>")
                    print(result)
                    print("\n")
                    miss = True
                    #mismatch_count += 1
                elif (result!=None):
                    if len(result) > 1 and expected_result != "non_dup":
                        expected_match_id = paper['_source']['labelled_duplicates']
                        if expected_match_id[0] not in result:
                            miss = True
                    elif len(result) == 1 and expected_result == "non_dup":
                        pass
                    else:
                        print(paper)
                        print(expected_result)

                        print(paper['_source']['labelled_duplicates'])
                        print(">>>>>>>>>>>>>>>>>>>>>>>>>>")
                        print(result)
                        print("\n")
                        miss = True
                #print(miss_cat_count["non_dup"])
                cat = paper['_source']['cat']
                miss_cat_count[cat] += 1 if (miss == True) else 0

        except Exception as es:
            print("exception in findMatchingDocumentsLSH with error msg: ", es)

if __name__ == "__main__":
    es = Elasticsearch([{'host': '130.203.139.160', 'port': 9200}])
    mismatch_count = 0
    l = [0, 4, 9]
    miss_cat_count = {"exact_dup": 0, "near_exact_dup": 0, "non_dup": 0}

    for i in l:
        res = es.search(index="dedupe_test", body = {
        "from": i*10000,
        'size' : 10000,
        'query': {
             "match_all": {
             }
        }
        })
        #print(res)
        dupe_ids = []
        docs = []
        for doc in res['hits']['hits']:
            id = doc['_source']['core_id']
            if (id in dupe_ids):
                pass
            else:
                docs.append(doc)
                dupe_id = doc['_source']['labelled_duplicates']
                dupe_ids.extend(dupe_id)

        print(len(docs))
        print("%d documents found" % res['hits']['total']['value'])
        data = [doc for doc in docs]
        findMatchingDocumentsLSH(data, miss_cat_count)

    print('miss classified documents --->', miss_cat_count)
