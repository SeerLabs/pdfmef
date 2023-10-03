from elasticsearch import Elasticsearch
es = Elasticsearch(["http://130.203.139.160:9200/"], verify_certs=True)

paperid = '79fd80bcfacc56113099d79440f9dd697ad53b3b'
indexname = 'csx_citeseer_docs_old_pubinfo'

if not es.ping():
    raise ValueError("Connection failed")
else:
    print("Connection Established !")

es.delete_by_query(index=indexname, body={
  "query": {
    "match": {
      "paper_id": paperid
    }
  }
})
