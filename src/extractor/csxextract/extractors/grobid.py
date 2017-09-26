from extraction.runnables import Extractor, RunnableError, ExtractorResult
import extractor.csxextract.interfaces as interfaces
import extractor.csxextract.config as config
import extractor.csxextract.filters as filters
import defusedxml.ElementTree as safeET
import xml.etree.ElementTree as ET
import xml.sax.saxutils as xmlutils
import requests
import re


# Returns full TEI xml document of the PDF
class GrobidTEIExtractor(interfaces.FullTextTEIExtractor):
   dependencies = frozenset([filters.AcademicPaperFilter])
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
      #print xml
      return ExtractorResult(xml_result=xml)

class GrobidCitationTEIExtractor(Extractor):
   dependencies = frozenset([filters.AcademicPaperFilter])
   result_file_name = '.cite.tei'

   def extract(self, data, dep_results):
      xml = _call_grobid_method(data, 'processReferences')
      return ExtractorResult(xml_result=xml)

def _call_grobid_method(data, method):
      url = '{0}/{1}'.format(config.GROBID_HOST, method)
      files = {'input': data}
      vars = {}
      #print url
      #print files['input']
      try:
         resp = requests.post(url, files=files, data=vars)
         # print 'TEXT: {0}'.format(resp.text)
      except requests.exceptions.RequestException as ex:
         raise RunnableError('Request to Grobid server failed')

      #print resp.status_code
      if resp.status_code != 200:
         raise RunnableError('Grobid returned status {0} instead of 200\nPossible Error:\n{1}'.format(resp.status_code, resp.text))

      # remove all namespace info from xml string
      # this is hacky but makes parsing it much much easier down the road
      remove_xmlns = re.compile(r'\sxmlns[^"]+"[^"]+"')
      remove_xsi = re.compile(r'\sxsi[^"]+"[^"]+"')
      xml_text = remove_xmlns.sub('', resp.content)
      xml_text = remove_xsi.sub('', xml_text)
      # print 'FORMATED: {0}'.format(xml_text)
      xml = safeET.fromstring(xml_text) # default

      # my_code
      #ET.register_namespace('','http://www.tei-c.org/ns/1.0')
      #xml = ET.fromstring(resp.text)
      #xml = safeET.fromstring(resp.text)  # default

      #print 'XML: {0}'.format(xml)
      return xml

