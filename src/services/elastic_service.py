from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, MultiSearch, Q
from elasticsearch_dsl.query import MoreLikeThis
import requests
import json

class ElasticService:

    def __init__(self):
        self.connection = Elasticsearch([{'host': '130.203.139.151', 'port': 9200}])

    def get_connection(self):
        return self.connection

    def test_connection(self):
        req = requests.get('http://130.203.139.151:9200')
        content = req.content
        parsed = json.loads(content)
        self.print_response(parsed)

    def print_response(self, response):
        # print(json.dumps(response.json(), indent=4, sort_keys=True))
        print(response['hits']['hits'])

    def paginated_search(self, index, query, page, pageSize, fields_to_search, source=None):
        s = Search(index=index, using=self.connection)

        if source:
            s.source(includes=[source])

        start = (page - 1) * pageSize
        s = s.query('multi_match', query=query, fields=fields_to_search)
        s = s[start:start + pageSize]

        response = s.execute()
        return response

    def paginated_search_with_ids(self, index, page, pageSize, ids, sort, source=None):
        s = Search(index=index, using=self.connection)

        if source:
            s.source(includes=[source])

        start = (page - 1) * pageSize
        s = s.query('ids', values=ids)
        s = s.sort(sort)
        s = s[start:start + pageSize]

        return s.execute()


    def more_like_this_search(self, index, id):
        s = Search(index=index, using=self.connection)
        s = s.query(MoreLikeThis(like={'_id': id, '_index': index}, fields=["title", "abstract"], min_term_freq=3, min_word_length=6, max_query_terms=12))
        response = s.execute()
        return response
