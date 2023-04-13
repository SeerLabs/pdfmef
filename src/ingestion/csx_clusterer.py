import time

import nltk
from elasticsearch import TransportError
from elasticsearch.helpers import bulk
from elasticsearch_dsl import Nested
from extractor.python_wrapper import utils, wrappers
from datasketch import MinHash, MinHashLSH

import configparser
import settings
from services.elastic_service import ElasticService
import logging

from collections import Counter
from typing import List
from utils.text_utils import remove_accents, strip_punctuation
from ingestion.interfaces import CSXClusterer
from models.elastic_models import Author, Cluster, KeyMap
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
import logging

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


logger = logging.getLogger(__name__)

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
                    self.merge_with_existing_cluster(matched_cluster_id=paper_id, current_paper=paper)
                    return
                else:
                    continue
        self.create_new_paper(paper)

    def cluster_paper_with_bm25_lsh(self, paper: Cluster) -> None:
        try:
            current_paper_title = paper.title
            config = configparser.ConfigParser()
            try:
                config.read("/pdfmef-code/src/extractor/python_wrapper/properties.config")
            except Exception as ex:
                print(ex)
            elasticConnectionProps = dict(config.items('ElasticConnectionProperties'))
            wrapper = wrappers.ElasticSearchWrapper(elasticConnectionProps)
            documents = wrapper.get_batch_for_lsh_matching(current_paper_title)
            has_new = False
            documents_to_be_similar = []
            paper_not_exists = True
            for doc in documents:
                try:
                    if paper.paper_id[0] not in doc['_source']['paper_id']:
                        documents_to_be_similar.append(doc)
                    else:
                        paper_not_exists = False
                except Exception:
                    documents_to_be_similar.append(doc)

            if (len(documents_to_be_similar) > 0 and paper_not_exists):
                documents = documents_to_be_similar
                similar_doc_id = self.find_similar_document(documents, current_paper_title)
                if similar_doc_id and len(similar_doc_id) > 0:
                    self.merge_with_existing_cluster(matched_cluster_id=similar_doc_id, current_paper=paper)
                else:
                    self.create_new_paper(paper)
            elif (len(documents_to_be_similar) == 0 and paper_not_exists):
                self.create_new_paper(paper)


        except Exception as ex:
            pass
            #print("exception in cluster_paper_with_bm25_lsh with msg-->", ex)

    def create_shingles(self, doc, k):
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

    def find_similar_document(self, documents, current_paper_title):

       if (documents == None or len(documents) == 0):
        return None
       # print("found matching documents without lsh ---->",documents[0]['_source']['paper_id'])
       # return documents[0]['_source']['paper_id']
       lsh = MinHashLSH(threshold=0.6, num_perm=128)
       for doc in documents:
            try:
                title = doc['_source']['title']
                id = doc['_id']
                d={}
                with_wildcard = False
                count = 0
                s = self.create_shingles(title, 5)
                min_hash = MinHash(num_perm=128)
                for shingle in s:
                    min_hash.update(shingle.encode('utf8'))
                if (not id in lsh):
                    lsh.insert(f"{id}", min_hash)
            except Exception as ex:
                print("hereeee lsh exception", ex)
                pass

       Title = current_paper_title
       s = self.create_shingles(Title, 5)
       min_hash = MinHash(num_perm=128)
       for shingle in s:
        min_hash.update(shingle.encode('utf8'))
       result = lsh.query(min_hash)
       if (len(result) >= 1):
        return result
       else:
        return None
        #print(result)

    def cluster_papers(self, papers: List[Cluster]):
        for paper in papers:
            self.create_new_paper_raw(paper)
            #self.cluster_paper_with_bm25_lsh(paper)

    def cluster_papers_bm25_lsh(self, papers: List[Cluster]):
        for paper in papers:
            self.cluster_paper_with_bm25_lsh(paper)

    def create_new_paper_raw(self, paper: Cluster):
        try:
            paper.save(using=self.elastic_service.get_connection())
        except Exception as e:
            print("failed creating new paper for paper id: "+paper.paper_id+" with error: "+e.info)
           #print(""e)
           #exit()


    def create_new_paper(self, paper: Cluster):
        try:
            paper.save(using=self.elastic_service.get_connection(), index=settings.CLUSTERS_INDEX)
        except Exception as e:
            print("failed creating new paper for paper id: "+paper.paper_id+" with error: "+e.info)
           #print(""e)
           #exit()

    def merge_with_existing_cluster(self, matched_cluster_id: str, current_paper: Cluster):
        try:
           print('found similar document with id-->',matched_cluster_id)
           try:
            print('current document title--->', current_paper.title)
            print('current document id--->', current_paper.paper_id)
           except Exception:
            pass
           resp = Cluster.search(using=self.elastic_service.get_connection()).filter("term", _id=matched_cluster_id[0])
           matched_cluster = resp.execute()[0]
           #print("hereeeee")
           #print(matched_cluster.paper_id)
           #matched_cluster = Cluster.get(using=self.elastic_service.get_connection(), id = matched_cluster_id)
        except Exception as ex:
            print('error here in  Cluster get --->', ex)
        if current_paper.has_pdf and matched_cluster.is_citation:
            matched_cluster.text = current_paper.text
            matched_cluster.pub_info = current_paper.pub_info
        if current_paper.is_citation:
            if matched_cluster.has_pdf:
                print("updating citation for the paper id --->", matched_cluster.paper_id)
                print("citation --->", current_paper.cited_by[0])
            matched_cluster.add_cited_by(current_paper.cited_by[0])
            matched_cluster.is_citation = True
        if current_paper.has_pdf:
            matched_cluster.has_pdf = True
            #matched_cluster.source_url = current_paper.source_url
            print("adding here")
            print(current_paper.paper_id[0])
            print(matched_cluster.paper_id)
            matched_cluster.add_paper_id(current_paper.paper_id[0])
            print(matched_cluster.paper_id)

        try:
            if not current_paper.is_citation and current_paper.source_url[0] not in matched_cluster.source_url:
                matched_cluster.add_source_url(current_paper.source_url[0])
                print("hereeeeeeeeee--------------------------------------")
                print(matched_cluster.source_url)
        except Exception:
            pass
        try:
            matched_cluster.save(using=self.elastic_service.get_connection(), index=settings.CLUSTERS_INDEX)
        except Exception as e:
            print("Exception occurred while merging with an existing cluster with error message: "+ e)

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
            author.surname = strip_punctuation(author.surname)

    @classmethod
    def _normalize_title(cls, text: str):
        if text is None:
            return ""
        ps = PorterStemmer()
        text = text.lower()
        text = strip_punctuation(text)
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
    l2 = "The MARCELL Legislative Corpus"
    # print(similarity(l1, l2))
    import elasticsearch
    import elasticsearch.helpers

    es = elasticsearch.Elasticsearch([{'host': '130.203.139.151', 'port': 9200}])
    results = elasticsearch.helpers.scan(es,
                                         index=settings.CRAWL_META_INDEX,
                                         preserve_order=True,
                                         query={"query": {"match_all": {}}})
    count = 0
    for item in results:
        s = Cluster.search(using=es)
        s = s.filter("term", paper_id=item['_id'])
        response = s.execute()

        if len(response) == 0:
            print(item['_id'], item['_source']['pdf_path'])
            count += 1
    print(count)
