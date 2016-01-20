import re
import xml.etree.ElementTree as ET
import subprocess32 as subproces
import extraction.utils as utils
from extraction.core import ExtractionRunner
from extraction.runnables import Filter, Extractor, ExtractorResult

# Define extractors and filters
class HasNumbersFilter(Filter):
   def filter(self, data, deps):
      success = re.search(r'[0-9]', data, re.UNICODE)
      return bool(success)

class EmailExtractor(Extractor):
   result_file_name = 'emails.xml'

   def extract(self, data, deps):
      emails = re.findall(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}\b',
                        data,
                        re.IGNORECASE | re.UNICODE)
      root = ET.Element('extraction')
      for email in emails:
         ele = ET.SubElement(root, 'email')
         ele.text = email

      return ExtractorResult(xml_result=root)

class LinesStartWithNumberExtractor(Extractor):
   dependencies = frozenset([HasNumbersFilter])

   def extract(self, data, deps):
      try:
         (status, stdout, stderr) = utils.external_process(['awk', '/^[0-9]/ {print;}', '-'], input_data=data, timeout=5)
      except subprocess.TimeoutExpired:
         raise RunnableError('awk timed out')

      lines = [line for line in stdout.split("\n") if line]

      root = ET.Element('extraction')
      for line in lines:
         ele = ET.SubElement(root, 'line')
         ele.text = line

      return ExtractorResult(xml_result=root)


# Set up and run extraction
extraction_runner = ExtractionRunner()
extraction_runner.add_runnable(HasNumbersFilter)
extraction_runner.add_runnable(EmailExtractor)
extraction_runner.add_runnable(LinesStartWithNumberExtractor)

extraction_runner.run(u'''Random data that contains some emails bob@example.com
Test lines with some @ signs now and then. Meet you@home@2p.m.
Line with another email embedded howie009@yahoo.com in the line.
jones@gmail.com fredie@emerson.retail.com
123 Some lines even start with numbers
Some lines don't start with numbers
004 The final line in the test data''', 'extraction/test/sample_output', run_name = 'Sample Data')


      
      
