from elasticsearch import Elasticsearch
from xml.dom.minidom import parseString
# import urllib2 as url
from urllib.request import urlopen
# import MySQLdb as mdb
import utils
import os
import sys

sys.path.append('../src')
import settings


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

class FileSystemWrapper(Wrapper):
    'Wrapper using file system and does not communicate with database'

    #Constructor
    #
    #Parameters: rootPath - path to directory that should be proccessed
    #               batchSize - number of documents to process at a time
    def __init__(self, rootPath, batchSize):
        self.batchSize = batchSize
        self.allDocs = []   #stores a list of paths to the documents to process
        self.rootPath = rootPath
        for path, subdirs, files in os.walk(rootPath):
            for name in files:
                if name[-3:] == 'pdf':
                    self.allDocs.append(os.path.join(path, name))
        self.batch = [] #stores a list of paths to the documents to process

    #get_document_batch()
    #Purpose: retrieves batch of documents to process from server
    def get_document_batch(self):
        self.batch = []
        for i in range(0, self.batchSize):
            if len(self.allDocs) > 0:
                self.batch.append(self.allDocs.pop())

    #get_document_ids()
    #
    #Purpose: parses the ids of all documents in a batch
    #Returns: list of string ids
    def get_document_ids(self):
        ids = []
        for docPath in self.batch:
            ids.append(utils.file_name_to_id(docPath[docPath.rfind('/') + 1 : docPath.rfind('.pdf') + 4]))
        return ids

    #get_document_paths()
    #
    #Purpose: parses the paths of all documents in a batch
    #Returns: list of document paths as strings
    def get_document_paths(self):
        paths = []
        for docPath in self.batch:
            paths.append(docPath.replace(self.rootPath, ''))
        return paths

    #update_state(ids, state)
    #
    #Purpose: updates the extraction state of the given documents in the database
    #Parameters: ids - list of documents ids, state - the int state to assignt to each document
    def update_state(self, ids, state):
        return

    #on_stop()
    #
    #Purpose: performs any necessary closing statements to free up connections and such
    def on_stop(self):
        return

#get_connection(host, dbName, user, pass)
#
#Purpose: gets a connection to the database that stores metadata
#Parameters: hostName - hostname that database is on, dbName - name of database,
#                       username, password
#Returns: MySQLConnection object

def get_connection(hostName, dbName, username, password, port):
    pass
    # try:
    #     #con = mdb.connect(user=username, passwd=password, host=hostName, db=dbName)
    #     con = mdb.connect(hostName, username, password, dbName, port)
    #     return con
    # except Exception as e:
    #     print ("Error %d: %s" % (e.args[0],e.args[1]))
    #     sys.exit(1)


class MySQLWrapper(Wrapper):
    'Wrapper using mySQL API'

    #Constructor
    #
    #Parameters: config - dict that holds configurations for a database connection,
    #               states - dict that holds map of state values
    def __init__(self, config, states):
        self.connection = get_connection(config['host'], config['database'], config['username'], config['password'], int(config['port']))
        self.batchSize = int(config['batchSize'])
        self.startID = config['startid']
        self.states = states
        self.batch = None   #stores a list of document ids

    #on_stop()
    #
    #Purpose: performs any necessary closing statements to free up connections and such
    #Behavior: closes database connection
    def on_stop(self):
        self.connection.close()

    #get_document_batch()
    #
    #Purpose: retrieves batch of documents to process from server
    def get_document_batch(self):
        cursor = self.connection.cursor()
        query = 'SELECT id from main_crawl_document WHERE id> %s and state = %s ORDER BY id LIMIT %s;'

        cursor.execute(query, (self.startID, self.states['crawled'], self.batchSize))

        ids = []
        docs = cursor.fetchall()
        for doc in docs:
            for idnum in doc:
                ids.append(str(idnum))

        self.batch = ids
        cursor.close()

    #get_document_ids()
    #
    #Purpose: parses the ids of all documents in a batch
    #Returns: list of string ids
    def get_document_ids(self):
        return self.batch

    #get_document_paths(docs)
    #
    #Purpose: parses the paths of all documents in a batch
    #Returns: list of document paths as strings
    def get_document_paths(self):
        paths = []
        for ID in self.batch:
            paths.append(utils.id_to_path(ID) + utils.id_to_file_name(ID) + '.pdf')
        print("mysql",paths)
        return paths

    #update_state(ids, state)
    #
    #Purpose: updates the extraction state of the given documents in the database
    #Parameters: ids - list of document ids, state - the int state to assignt to each document
    def update_state(self, ids, state):
        cursor = self.connection.cursor()
        statement = 'UPDATE main_crawl_document SET state = {0} where id in ({1});'

        idString = ''

        for doc in ids:
            if len(idString) != 0:
                idString += ','
            idString += str(doc)

        statement = statement.format(state, idString)
        #print(statement)
        cursor.execute(statement)

        self.connection.commit()


class HTTPWrapper(Wrapper):
    'Wrapper using the RESTful API'

    #Constructor
    #
    #Parameters: config - dict that holds configurations for a database connection
    def __init__(self, config):
        self.host = config['host']
        self.key = config['key']
        self.batchSize = int(config['batchsize'])
        self.batch = None #stores a DOM with ids and paths

    #get_document_batch()
    #
    #Purpose: retrieves batch of documents to process from server
    def get_document_batch(self):
        request = 'http://' + self.host + '/api/getdocs.xml?key=' + self.key + '&n=' + str(self.batchSize)
        responseString = urlopen(request).read()
        response = parseString(responseString)
        docs = response.getElementsByTagName('doc')
        self.batch = docs

    #get_document_ids()
    #
    #Purpose: parses the ids of all documents in a batch
    #Returns: list of string ids
    def get_document_ids(self):
        ids = []
        for element in self.batch:
            ids.append(element.getAttribute('id'))
        return ids

    #get_document_paths(docs)
    #
    #Purpose: parses the paths of all documents in a batch
    #Returns: list of document paths as strings
    def get_document_paths(self):
        paths = []
        for element in self.batch:
            paths.append(element.firstChild.nodeValue)
        return paths

    #update_state(ids, state)
    #
    #Purpose: updates the extraction state of the given documents in the database
    #Parameters: ids - list of documents ids, state - the int state to assignt to each document
    def update_state(self, ids, state):
        idString = ''
        for doc in ids:
            idString = idString + str(doc) + ','
        if len(idString) > 0:
            idString = idString[:-1]
            request = 'http://' + self.host + '/api/setdocs.xml?key=' + self.key + '&ids=' + idString + '&state=' + str(state)
            response = urlopen(request).getcode()

    #on_stop()
    #
    #Purpose: perform necessary closing statements
    #Behavior: nothing to do
    def on_stop(self):
        print('closed')


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
        results = self.get_connection().search(index=settings.S2_META_INDEX, body=body)
        self.s2_batch = results['hits']['hits']

    def get_s2_batch_for_lsh_matching(self, author, year):
        """Purpose: retrieves batch of documents to process from server"""
        print("inside get_s2_batch_for_lsh_matching---> \n")
        body = {
                 "from": 0,
                 "size": 1000,
                 "query": {
                   "bool": {
                     "must": [
                      {
                          "match": {
                            "authors.name.keyword": author
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
        self.s2_batch = results['hits']['hits']

    def get_document_batch_citation(self, ES_index_name):
        """Purpose: retrieves batch of documents to process from server"""
        body = {
                 "from": 0,
                 "size": self.batchSize,
                 "query": {
                   "bool": {
                     "must": [
                       {
                         "term": {
                           "has_pdf": True
                         }
                       },
                       {
                         "multi_match": {
                           "query": "fresh",
                           "fields": "text_status"
                         }
                       }
                     ]
                   }
                 }
               }

        results = self.get_connection_prod().search(index=ES_index_name, body=body)
        self.batch = []
        for result in results['hits']['hits']:
            if (result["_id"] == '_update'):
                pass
            else:
                self.batch.append(result)
        return self.batch


    def get_cluster_document_batch(self):
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

        results = self.get_connection_prod().search(settings.RAW_PAPERS_INDEX, body=body)
        self.batch = []
        for result in results['hits']['hits']:
            if (result["_id"] == '_update'):
                pass
            else:
                self.batch.append(result)

    def get_document_batch(self, ES_index_name):
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

        results = self.get_connection().search(ES_index_name, body=body)
        self.batch = []
        for result in results['hits']['hits']:
            if (result["_id"] == '_update'):
                pass
            else:
                self.batch.append(result)

    def get_batch_for_lsh_matching(self, title):
        """Purpose: retrieves batch of documents to process from server"""

        body = ""
        matching_docs = []
        try:
            body = {
                        "size": 100,
                        "query":{
                          "bool":{
                             "should":
                                {
                                   "match":{
                                      "title":{
                                         "query": title,
                                         "minimum_should_match":"75%"
                                      }
                                   }
                                }
                          }
                        }
                   }
            results = self.get_connection_prod().search(index=settings.CLUSTERS_INDEX, body=body)
            matching_docs = results['hits']['hits']
        except Exception as ex:
            pass
        return matching_docs

    def get_doc_with_id(self, doc_id):
        body = ""
        try:
            body = {
                "query": {
                    "multi_match": {
                        "query": doc_id,
                        "fields": "paper_id"
                    }
                }
            }
        except Exception:
            pass
        results = self.get_connection_prod().search(index=settings.CLUSTERS_INDEX, body=body)
        self.s2_batch = results['hits']['hits']
        return self.s2_batch

    def update_document_with_fields(self, doc_id, cited_by):
        source_to_update = {
            "doc" : {
                "cited_by" : cited_by
            }
        }
        response = self.get_connection_prod().update(index=settings.CLUSTERS_INDEX, id=doc_id, body=source_to_update)


    def update_raw_paper_status(self, doc_ids):
        for doc_id in doc_ids:
            source_to_update = {
                "doc" : {
                    "text_status" : "done"
                }
            }
            response = self.get_connection_prod().update(index=settings.RAW_PAPERS_INDEX, id=doc_id, body=source_to_update)

    def update_citation_status(self, doc_ids):
        for doc_id in doc_ids:
            source_to_update = {
                "doc" : {
                    "text_status" : "done"
                }
            }
            response = self.get_connection_prod().update(index=settings.CLUSTERS_INDEX, id=doc_id, body=source_to_update)

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
            try:
                strr = str(element['_source']['pdf_path'])
                if strr.endswith('\n'):
                    strr = strr[:-1]
                paths.append(strr)
                self.file_path_sha1_mapping[strr] = element['_id']
                self.file_path_source_url_map[strr] = element['_source']['source']
            except Exception:
                pass
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