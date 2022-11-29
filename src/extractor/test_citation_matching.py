import configparser
import functools
import configparser
from datasketch import MinHash, MinHashLSH
from elasticsearch import Elasticsearch
from extractor.python_wrapper import utils, wrappers
from ingestion.csx_extractor import CSXExtractorImpl
import re

def findMatchingDocumentsLSH(papers):
    config = configparser.ConfigParser()
    mismatch_count = 0
    try:
        config.read("/pdfmef-code/src/extractor/python_wrapper/properties.config")
    except Exception as ex:
        print(ex)
    elasticConnectionProps = dict(config.items('ElasticConnectionProperties'))
    wrapper = wrappers.ElasticSearchWrapper(elasticConnectionProps)
    import re
    for paper in papers:
        try:
            if (True):
                title = paper['_source']['processed_title']
                title = re.sub(r"[^a-zA-Z0-9 ]", "", title)
                print(title)
                documents = wrapper.get_batch_for_lsh_matching(title)
                lsh = MinHashLSH(threshold=0.90, num_perm=128)
                print(len(documents))
                for doc in documents:
                    try:
                        print("----------here--------------")
                        title = doc['_source']['processed_title']
                        title = re.sub(r"[^a-zA-Z0-9 ]", "", title)
                        print(title)
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

                print("------------------incoming document title---------------------------")
                Title = paper['_source']['processed_title']
                Title = re.sub(r"[^a-zA-Z0-9 ]", "", Title)
                print(Title)
                #Title = re.sub(r'\s+', ' ', Title)
                s = CSXExtractorImpl().create_shingles(Title, 5)
                min_hash = MinHash(num_perm=128)
                for shingle in s:
                    min_hash.update(shingle.encode('utf8'))
                result = lsh.query(min_hash)
                expected_result = paper['_source']['cat']
                print(expected_result)
                #print(paper)
                #print('<---------------------------------------------------------->')
                if (len(result) <=1 and expected_result != "non_dup"):
                    print(expected_result)
                    print(paper['_source']['labelled_duplicates'])
                    print(">>>>>>>>>>>>>>>>>>>>>>>>>>")
                    print(result)
                    print("\n")
                    mismatch_count += 1
                elif (result!=None):
                    if len(result) > 1 and expected_result != "non_dup":
                        expected_match_id = paper['_source']['labelled_duplicates']
                        print(paper['_source']['cat'])
                        print(expected_match_id)
                        print(">>>>>>>>>>>>>>>>>>>>>>>>>>")
                        print(result)
                        print("\n")
                        if expected_match_id[0] not in result:
                            mismatch_count += 1
                    elif len(result) == 1 and expected_result == "non_dup":
                        pass
                    else:
                        print(paper)
                        print(expected_result)

                        print(paper['_source']['labelled_duplicates'])
                        print(">>>>>>>>>>>>>>>>>>>>>>>>>>")
                        print(result)
                        print("\n")
                        mismatch_count += 1

        except Exception as es:
            print("exception in findMatchingDocumentsLSH with error msg: ", es)
    return mismatch_count

if __name__ == "__main__":
    es = Elasticsearch([{'host': '130.203.139.160', 'port': 9200}])
    mismatch_count = 0
    l = [0]
    for i in l:
        res = es.search(index="dedupe_test", body = {
        "from": i*10000,
        'size' : 10,
        'query': {
             "match": {
                "core_id.keyword": "29509937"
             }
        }
        })
        #print(res)
        print("%d documents found" % res['hits']['total']['value'])
        data = [doc for doc in res['hits']['hits']]
        mismatch_count += findMatchingDocumentsLSH(data)
    print('miss classified documents --->', mismatch_count)
