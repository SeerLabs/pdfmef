from extraction.runnables import Extractor, Filter

class PlainTextExtractor(Extractor):
   # Extractors extending this extractor should:
   # return an ExtractorResult such that
   #    xml_result is a node named 'file' with content 'plain_text.txt'
   #    files is a dict with a key 'plain_text.txt' and a value which is the plain text of the pdf
   #      the plain text should be a normal string. So extractors working with the text in the future should
   #      first decode it to utf-8
   def extract(self, data, dependency_results):
      raise NotImplementedError('Extend me!')

class HeaderTEIExtractor(Extractor):
   def extract(self, data, dependency_results):
      raise NotImplementedError('Extend me!')

class FullTextTEIExtractor(HeaderTEIExtractor):
   # Extractors extending the extractor should:
   # return an ExtractorResult object such that
   #  xml_result is the root node of a TEI xml document
   # The TEI document should contain header, text, and reference information
   def extract(self, data, dependency_results):
      raise NotImplementedError('Extend me!')

class CSXHeaderExtractor(Extractor):
   # Returns an ExtractorResult object such that
   #   xml_result is an xml document containing header info in the CSX ingestion format
   def extract(self, data, dependency_results):
      raise NotImplementedError('Extend me!')

class CSXCitationExtractor(Extractor):
   # Returns an ExtractorResult object such that
   #   xml_result is an xml document containing citation info in the CSX ingestion format
   def extract(self, data, dependency_results):
      raise NotImplementedError('Extend me!')

