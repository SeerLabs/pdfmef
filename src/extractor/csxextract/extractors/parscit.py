from extraction.runnables import Extractor, RunnableError, ExtractorResult
import extraction.utils
import extractor.csxextract.config as config
import extractor.csxextract.interfaces as interfaces
import extractor.csxextract.filters as filters
import extractor.csxextract.utils as utils
import defusedxml.ElementTree as safeET
import xml.etree.ElementTree as ET
import subprocess32 as subprocess
import requests
import os
import shutil
import glob
import re
import tempfile
import logging

logger = logging.getLogger(__name__)
# Takes a plain text version of a PDF and uses ParsCit to extract citations
# Returns an xml document of citation info in CSX format
class ParsCitCitationExtractor(interfaces.CSXCitationExtractor):
   dependencies = frozenset([interfaces.PlainTextExtractor, filters.AcademicPaperFilter])

   result_file_name = '.cite'

   def extract(self, data, dependency_results):
      # Get the plain text file of the PDF and write it to a temporary location
      pdf_text = dependency_results[interfaces.PlainTextExtractor].files['.txt']
      text_file_path = extraction.utils.temp_file(pdf_text)

      # Run parscit on the text file to extract citations
      try:
         status, stdout, stderr = extraction.utils.external_process(['perl', config.PARSCIT_PATH, text_file_path], timeout=20)
      except subprocess.TimeoutExpired as te:
         logger.error('ParsCit timed out while processing document')
         raise RunnableError('ParsCit timed out while processing document')
      finally:
         os.remove(text_file_path)

      if status != 0:
         logger.error('ParsCit Failure. Possible error:\n' + stderr)
         raise RunnableError('ParsCit Failure. Possible error:\n' + stderr)

      # ParsCit will give us a string representing an xml doc
      # convert from string type  into an xml object
      xml = safeET.fromstring(stdout)

      return ExtractorResult(xml_result=xml)


