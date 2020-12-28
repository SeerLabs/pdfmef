import time

import nltk
from elasticsearch import TransportError, Elasticsearch
from elasticsearch.helpers import bulk
from elasticsearch_dsl import Nested, MultiSearch, Search

from services.elastic_service import ElasticService
# from services.elasticsearch_adapters import ClusterAdapter

from collections import Counter
from typing import List
from utils.text_utils import remove_accents, strip_punctuation
from ingestion.interfaces import CSXClusterer
from models.elastic_models import Author, Cluster, KeyMap
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords

_author_ = "Sai Raghav Keesara"
_copyright_ = "Copyright 2020, Penn State University"
_license_ = ""
_version_ = "1.0"
_maintainer_ = "Sai Raghav Keesara"
_email_ = "sai@psu.edu"
_status_ = "Development"

nltk.download('stopwords')

stopwords_dict = Counter(stopwords.words("english"))
name_join_words = Counter(["van", "von", "der", "den", "di", "de", "le"])


class KeyMatcherClusterer(CSXClusterer):

    def __init__(self):
        self.key_generator = KeyGenerator()
        self.elastic_service = ElasticService()

    def cluster_paper(self, paper: Cluster) -> None:
        current_keys = paper.keys
        found_keys = []
        if len(current_keys) > 0:
            found_keys = KeyMap.mget(docs=current_keys, using=self.elastic_service.get_connection(), missing='skip')
        if len(found_keys) > 0:
            for each_key in found_keys:
                paper_id = each_key.paper_id
                found_paper = Cluster.get(id=paper_id, _source=['title'], using=self.elastic_service.get_connection())
                if similarity(found_paper.title, paper.title) > 0.60:
                    self.merge_with_existing_paper(matched_paper_id=paper_id, current_paper=paper)
                    return
                else:
                    continue
        self.create_new_paper(paper)

    def cluster_papers(self, papers: List[Cluster]):
        for paper in papers:
            self.cluster_paper(paper)

    def create_new_paper(self, paper: Cluster):
        try:
            paper.save(using=self.elastic_service.get_connection())
            keymaps = []
            for key in paper.keys:
                km = KeyMap()
                km.meta.id = key
                km.paper_id = paper.meta.id
                keymaps.append(km.to_dict(include_meta=True))
            bulk(client=self.elastic_service.get_connection(), actions=iter(keymaps), stats_only=True)
        except TransportError as e:
            print(e.info)
            exit()

    def merge_with_existing_paper(self, matched_paper_id: str, current_paper: Cluster):
        matched_cluster = Cluster.get(id=matched_paper_id, using=self.elastic_service.get_connection())

        if current_paper.has_pdf and matched_cluster.is_citation:
            matched_cluster.text = current_paper.text
        if current_paper.is_citation:
            matched_cluster.add_cites(current_paper.cites[0])
            matched_cluster.is_citation = True
        if current_paper.has_pdf:
            matched_cluster.has_pdf = True
            matched_cluster.add_paper_id(current_paper.paper_id[0])

        try:
            matched_cluster.save(using=self.elastic_service.get_connection())
        except TransportError as e:
            time.sleep(5)
            self.merge_with_existing_paper(matched_paper_id, current_paper)

    def recluster_paper(self, paper: Cluster):
        pass

class KeyGenerator:

    def get_keys(self, title: str, authors: List[Author]):
        keys = []
        title_keys = self._get_title_keys(title)
        author_keys = self._get_author_keys(authors)

        if len(title_keys) == 0 or len(author_keys) == 0:
            return keys

        for author_key in author_keys:
            for title_key in title_keys:
                author_key = author_key.strip()
                title_key = title_key.strip()
                if title_key != "" and author_key != "":
                    keys.append(author_key + "_" + title_key)
        return keys

    def _get_title_keys(self, title: str):
        keys = []
        title = self._normalize_title(title)
        self._build_title_key(keys, title)
        offset_title = " ".join(title.split()[1:-1])
        if offset_title is not title and len(offset_title) > 1:
            self._build_title_key(keys, offset_title)
        self._build_title_key(keys, title)
        return keys

    def _get_author_keys(self, authors: List[Author]):
        author_keys = []
        if authors is None or len(authors) == 0:
            return author_keys
        self._normalize_authors(authors)
        for author in authors:
            if 'surname' in author:
                author_keys.append(author.surname)
        return author_keys

    @classmethod
    def _build_title_key(cls, keys: List[str], title: str):
        title = title.replace(" ", "")
        if len(title) > 30:
            title = title[:30]
        if len(title) >= 5:
            keys.append(title)

    @classmethod
    def _normalize_authors(cls, authors: Nested(Author)):
        for author in authors:
            if 'surname' not in author.to_dict(skip_empty=False):
                continue
            author.surname = author.surname.lower()
            remove_accents(author.surname)
            author.surname = ''.join([name for name in author.surname.split() if name not in name_join_words])
            strip_punctuation(author.surname)

    @classmethod
    def _normalize_title(cls, text: str):
        if text is None:
            return ""
        ps = PorterStemmer()
        text = text.lower()
        strip_punctuation(text)
        text = ' '.join([ps.stem(word) for word in text.split() if word not in stopwords_dict])
        return text.strip()

def normalize(text):
    text = text.lower()
    text.replace(" ", "")
    ''.join(e for e in text if e.isalnum())
    return text

def similarity(text1, text2):
    text1 = normalize(text1)
    text2 = normalize(text2)
    list1 = [text1[i:i + 3] for i in range(len(text1) - 3 + 1)]
    list2 = [text2[i:i + 3] for i in range(len(text2) - 3 + 1)]
    intersection = len(list(set(list1).intersection(list2)))
    union = (len(list1) + len(list2)) - intersection
    jaccard = float(intersection) / union
    containment = float(intersection) / min(len(list1), len(list2))
    return 2 * jaccard * containment / (jaccard + containment)

if __name__ == "__main__":
    l1 = "Evaluating Language Tools for Fifteen EU-official Under-resourced Languages"
    #l2 = "The MARCELL Legislative Corpus"
    #print(similarity(l1, l2))
    import elasticsearch
    import elasticsearch.helpers

    es = elasticsearch.Elasticsearch([{'host': '130.203.139.151', 'port': 9200}])
    results = elasticsearch.helpers.scan(es,
                                         index="crawl_meta",
                                         preserve_order=True,
                                         query={"query": {"match_all": {}}},
                                         )
    count = 0
    for item in results:
        #print(item['_id'], item['_source']['pdf_path'])
        s = Cluster.search(using=es)
        s = s.filter("term", paper_id=item['_id'])
        response = s.execute()

        if len(response) is 0:
            print(item['_id'], item['_source']['pdf_path'])
            count += 1
    print(count)
