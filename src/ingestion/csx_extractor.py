__author__ = "Sai Raghav Keesara"
__copyright__ = "Copyright 2020, Penn State University"
__license__ = ""
__version__ = "1.0"
__maintainer__ = "Sai Raghav Keesara"
__email__ = "sai@psu.edu"
__status__ = "Development"

import re

import xml.sax.saxutils as xmlutils

from ingestion.csx_clusterer import KeyGenerator
from ingestion.interfaces import CSXExtractor
from xml.etree.ElementTree import parse, tostring
from models.elastic_models import Cluster, Author, PubInfo
import functools

class CSXExtractorImpl(CSXExtractor):

    def batch_extract_textual_data(self, dirPath):
        pass

    def extract_figures(self, filepath):
        pass

    def batch_extract_figures(self, dirPath):
        pass

    def extract_textual_data(self, filepath):
        tei_root = parse(filepath)
        papers = []
        paper = Cluster()
        tei_filename = str(filepath[str(filepath).rfind('/')+1:])
        paper_id = tei_filename[:tei_filename.rfind('.')]
        paper.add_paper_id(paper_id)
        paper.title = self.extract_title_from_tei_root(tei_root)
        paper.abstract = self.extract_abstract(tei_root)
        paper.pub_info = self.extract_paper_pub_info_from_tei_root(tei_root)
        paper.authors = self.extract_authors_from_tei_root(tei_root)
        paper.has_pdf = True
        paper.is_citation = False
        citations = self.extract_citations_from_tei_root(tei_root=tei_root, paper_id=paper_id)
        paper.text = self.extract_text_from_tei_root(tei_root)
        paper.keys = KeyGenerator().get_keys(paper.title, paper.authors)
        papers.append(paper)
        papers.extend(citations)
        return papers

    @classmethod
    def extract_affiliations(cls, affiliation_node):
        org_name_nodes = affiliation_node.findall('./orgName')

        # orders org_name nodes
        def compare(n1, n2):
            # types of orgNames in order from least to most important this means
            # institution nodes should come first, then department, then laboratory, then any others
            types = ['laboratory', 'department', 'institution']
            score1 = (0 if not n1.get('type') in types else types.index(n1.get('type')))
            score2 = (0 if not n2.get('type') in types else types.index(n2.get('type')))
            score = -cmp(score1, score2)

            if score != 0:
                return score
            # if same type or orgName nodes, then order by the key attribute
            else:
                return cmp(n1.get('key', ''), n2.get('key', ''))

        def cmp(a, b):
            return (a > b) - (a < b)

        sorted(org_name_nodes, key=functools.cmp_to_key(compare))
        return ', '.join([n.text for n in org_name_nodes])

    @classmethod
    def extract_authors_from_tei_root(cls, tei_root):
        """Retreive author names from TEI doc"""
        namespaces = {'ns1': 'http://www.tei-c.org/ns/1.0'}
        authors = tei_root.findall('./teiHeader//biblStruct//author')
        paper_authors = []
        if authors is None:
            return paper_authors
        for author_node in authors:
            forename = ''
            if author_node.find("./ns1:persName/ns1:forename", namespaces) is not None:
                forename = author_node.find("./ns1:persName/ns1:forename", namespaces).text
            surname = ''
            if author_node.find("./ns1:persName/ns1:surname", namespaces) is not None:
                surname = author_node.find("./ns1:persName/ns1:surname", namespaces).text
            email = ''
            if author_node.find("./email") is not None:
                email = author_node.find("./email").text
            author = Author(forename=forename, surname=surname, email=email)
            # Find and output affiliation-related info
            affiliations = author_node.findall('./affiliation')
            if affiliations:
                # Use a pipe to delimit seperate affiliations
                affiliation_str = " | ".join(map(cls.extract_affiliations, affiliations))
                author.affiliation = affiliation_str
            paper_authors.append(author)
        return paper_authors

    @classmethod
    def extract_title_from_tei_root(cls, tei_root):
        title_node = tei_root.find('./teiHeader//titleStmt/title')
        if title_node is not None and title_node.text is not None:
            return title_node.text
        return ''

    @classmethod
    def xml_to_plain_text(cls, xml_string):
        remove_tags = re.compile(r'\s*<.*?>', re.DOTALL | re.UNICODE)
        plain_text = remove_tags.sub('\n', xml_string)
        # run this twice for weird situations where things are double escaped
        plain_text = xmlutils.unescape(plain_text, {'&apos;': "'", '&quot;': '"'})
        plain_text = xmlutils.unescape(plain_text, {'&apos;': "'", '&quot;': '"'})

        return plain_text.strip()

    @classmethod
    def extract_abstract(cls, tei_root):
        abstract_node = tei_root.find('./teiHeader/profileDesc/abstract')
        abstract = ""
        if abstract_node is not None:
            xml_string = tostring(abstract_node).decode('utf-8')
            remove_heading = re.compile(r'\s*<head.*?>.*?<\s*/\s*head>', re.DOTALL | re.UNICODE)
            xml_string = remove_heading.sub('', xml_string)
            abstract = cls.xml_to_plain_text(xml_string)
        return abstract

    @classmethod
    def extract_citations_from_tei_root(cls, tei_root, paper_id):
        citations = []
        """Retrieve author names from TEI doc"""
        namespaces = {'ns1': 'http://www.tei-c.org/ns/1.0'}
        citations_node = tei_root.findall('./text//listBibl//biblStruct')
        if citations_node is None:
            return citations
        for citation_node in citations_node:
            citation = Cluster()

            citation.add_cites(paper_id)
            # Citation Title
            if citation_node.find('./analytic/title') is not None:
                citation.title = citation_node.find('./analytic/title').text
            elif citation_node.find('./monogr/title') is not None:
                citation.title = citation_node.find('./monogr/title').text
            else:
                citation.title = ''

            # Citation Pub Info
            if citation_node.find('./monogr') is not None:
                citation.pub_info = cls.extract_pub_info_from_bibil_node(citation_node)

            # raw citation info
            # if citation_node.find('./note') is not None:
            #     citation.raw = citation_node.find('./note').text

            # Citation Authors
            if citation_node.findall('./analytic/author') is not None and len(
                    citation_node.findall('./analytic/author')):
                authors_node = citation_node.findall('./analytic/author')
            elif citation_node.findall('./monogr/author') is not None:
                authors_node = citation_node.findall('./monogr/author')
            else:
                authors_node = []

            for author_node in authors_node:
                author = Author()
                if author_node.find("./ns1:persName/ns1:surname", namespaces) is not None:
                    author.surname = author_node.find("./ns1:persName/ns1:surname", namespaces).text
                if author_node.find("./ns1:persName/ns1:forename", namespaces) is not None:
                    author.forename = author_node.find("./ns1:persName/ns1:forename", namespaces).text
                citation.authors.append(author)
            citation.extend_keys(KeyGenerator().get_keys(citation.title, citation.authors))
            citation.is_citation = True
            citation.has_pdf = False
            citations.append(citation)
        return citations

    @classmethod
    def extract_text_from_tei_root(cls, tei_root):
        body_node = tei_root.find('./text/body')
        if body_node is None:
            return ""
        xml_string = tostring(body_node).decode('utf-8')
        plain_text = cls.xml_to_plain_text(xml_string)
        return plain_text

    @classmethod
    def extract_pub_info_from_bibil_node(cls, bibilnode):
        pub_info = PubInfo()
        if bibilnode is None:
            return pub_info
        if bibilnode.find('./monogr') is not None:
            if bibilnode.find('./monogr/imprint/publisher') is not None:
                pub_info.publisher = bibilnode.find('./monogr/imprint/publisher').text
            if bibilnode.find('./monogr/imprint/date') is not None:
                if 'when' in bibilnode.find('./monogr/imprint/date').keys():
                    date_found = bibilnode.find('./monogr/imprint/date').get('when', default=0)
                    pub_info.date = date_found
                    pub_info.year = date_found.split("-")[0]
                else:
                    date_found = bibilnode.find('./monogr/imprint/date').text
                    if date_found is not None:
                        pub_info.date = date_found
                        pub_info.year = date_found[-4:]
            if bibilnode.find('./monogr/meeting/address') is not None:
                addr_str = ""
                for each_node in bibilnode.findall('./monogr/meeting/address/addrLine'):
                    if each_node.find('./addrLine') is not None:
                        addr_str = addr_str + ";" + each_node.find('./addrLine').text
                if bibilnode.findall('./monogr/meeting/address/addrLine') is not None:
                    for each_node in bibilnode.findall('./monogr/meeting/address/addrLine'):
                        addr_str = addr_str + " " + each_node.text
                pub_info.pub_address = addr_str
            if bibilnode.find('./monogr/meeting') is not None:
                pub_info.meeting = bibilnode.find('./monogr/meeting').text
            if bibilnode.find('./monogr/imprint/pubPlace') is not None:
                pub_info.pub_place = bibilnode.find('./monogr/imprint/pubPlace').text
            if bibilnode.find('./monogr/title') is not None:
                pub_info.title = bibilnode.find('./monogr/title').text
        return pub_info

    @classmethod
    def extract_paper_pub_info_from_tei_root(cls, tei_root):
        pub_info = cls.extract_pub_info_from_bibil_node(tei_root.find('./teiHeader/fileDesc/sourceDesc/biblStruct'))
        pub_stmt_node = tei_root.find('./teiHeader/fileDesc/publicationStmt')
        if pub_stmt_node is not None:
            if pub_stmt_node.find('./publisher') is not None:
                pub_info.publisher = pub_stmt_node.find('./publisher').text

            if pub_stmt_node.find('./date') is not None:
                if 'when' in pub_stmt_node.find('./date'):
                    date_found = pub_stmt_node.find('./date').attrib['when']
                    pub_info.date = date_found
                    pub_info.year = date_found.split("-")[0]
                else:
                    date_found = pub_stmt_node.find('./date').text
                    pub_info.date = date_found
                    pub_info.year = date_found[-4:]
        return pub_info


if __name__ == "__main__":
    extractor = CSXExtractorImpl()
    paper = extractor.extract_textual_data("../../test/resources/sample_tei.tei")
