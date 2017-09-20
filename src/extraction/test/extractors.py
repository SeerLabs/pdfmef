from extraction.runnables import Extractor, RunnableError, ExtractorResult
import extraction.test.filters as filters
import xml.etree.ElementTree as ET

class NothingExtractor(Extractor):
   def extract(self, data, dep_results):
      return ExtractorResult(xml_result=None)

class SelfExtractor(Extractor):
   def extract(self, data, dep_results):
      ele = ET.Element('result')
      ele.text = data
      return ExtractorResult(ele)

class SelfLogExtractor(Extractor):
   def extract(self, data, dep_results):
      self.log(data)
      ele = ET.Element('result')
      ele.text = data
      return ExtractorResult(ele)

class SelfChangeNameExtractor(Extractor):
   result_file_name = 'name.extension'
   def extract(self, data, dep_results):
      ele = ET.Element('result')
      ele.text = data
      return ExtractorResult(ele)
      

class ErrorExtractor(Extractor):
   def extract(self, data, dep_results):
      raise RunnableError('I always Error!')

class DepsOnErrorExtractor(Extractor):
   dependencies = frozenset([ErrorExtractor])

   def extract(self, data, dep_results):
      ele = ET.Element('result')
      ele.text = data
      return ExtractorResult(ele)

class DepsOnErrorExtractor2(Extractor):
   dependencies = frozenset([DepsOnErrorExtractor])
   def extract(self, data, dep_results):
      ele = ET.Element('result')
      ele.text = data
      return ExtractorResult(ele)

class FailingDepsExtractor(Extractor):
   dependencies = frozenset([filters.FailFilter])

   def extract(self, data, dep_results):
      return RunnableError('This extractor should never run!')

class PassingDepsExtractor(Extractor):
   dependencies = frozenset([filters.PassFilter])

   def extract(self, data, dep_results):
      ele = ET.Element('result')
      ele.text = data
      return ExtractorResult(ele)

#Extractors that extend this extractor should generate a file named 'test.txt' with the content 'test test'
class TestFileExtractor(Extractor):
   def extract(self, data, dep_results):
      raise RunnableError('This Extractor Should Be Extended')

class ImplTestFileExtractor(TestFileExtractor):
   def extract(self, data, dep_results):
      ele = ET.Element('file')
      ele.text = 'test.txt'
      files = {'test.txt': 'test test'}
      return ExtractorResult(ele, files=files)

class DepsOnTestFileExtractor(Extractor):
   dependencies = frozenset([TestFileExtractor])

   def extract(self, data, dep_results):
      return dep_results[TestFileExtractor]


