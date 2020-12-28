from extraction.runnables import Extractor, RunnableError, ExtractorResult
import extractor.csxextract.interfaces as interfaces
import extractor.csxextract.config as config
import extractor.csxextract.filters as filters
import defusedxml.ElementTree as safeET
import xml.etree.ElementTree as ET
import xml.sax.saxutils as xmlutils
import extraction.utils
import tempfile
import requests
import re
import os


# Returns full TEI xml document of the PDF
class GrobidTEIExtractor(interfaces.FullTextTEIExtractor):
   dependencies = frozenset([filters.SimpleAcademicPaperFilter])
   result_file_name = '.tei'

   def extract(self, data, dep_results):
      xml = _call_grobid_method(data, 'processFulltextDocument')
      return ExtractorResult(xml_result=xml)

# Returns TEI xml document only of the PDF's header info
class GrobidHeaderTEIExtractor(interfaces.HeaderTEIExtractor):
   dependencies = frozenset([filters.AcademicPaperFilter])
   result_file_name = '.header.tei'

   def extract(self, data, dep_results):
      xml = _call_grobid_method(data, 'processHeaderDocument')
      return ExtractorResult(xml_result=xml)

class GrobidCitationTEIExtractor(Extractor):
   dependencies = frozenset([filters.AcademicPaperFilter])
   result_file_name = '.cite.tei'

   def extract(self, data, dep_results):
      xml = _call_grobid_method(data, 'processReferences')
      return ExtractorResult(xml_result=xml)

def _call_grobid_method(data, method):
      url = '{0}/api/{1}'.format(config.GROBID_HOST, method)
      # Write the pdf data to a temporary location so Grobid can process it
      path = extraction.utils.temp_file(data, suffix='.pdf')
      files = {'input': (path, open(path, 'rb')),}
      try:
         resp = requests.post(url, files=files)
      except requests.exceptions.RequestException as ex:
         raise RunnableError('Request to Grobid server failed')
      finally:
         os.remove(path)

      if resp.status_code != 200:
         raise RunnableError('Grobid returned status {0} instead of 200\nPossible Error:\n{1}'.format(resp.status_code, resp.text))

      # remove all namespace info from xml string
      # this is hacky but makes parsing it much much easier down the road
      #remove_xmlns = re.compile(r'\sxmlns[^"]+"[^"]+"')
      #xml_text = remove_xmlns.sub('', resp.content)
      #xml = safeET.fromstring(xml_text)
      xmlstring = re.sub(' xmlns="[^"]+"', '', resp.content.decode('utf-8'), count=1)
      xml = safeET.fromstring(xmlstring)

      return xml

