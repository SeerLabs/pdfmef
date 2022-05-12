from extraction.runnables import Extractor, RunnableError, ExtractorResult
import extractor.csxextract.interfaces as interfaces
import extractor.csxextract.config as config
import extraction.utils
import subprocess32 as subprocess
import defusedxml.ElementTree as safeET
import xml.etree.ElementTree as ET
import os
import tempfile
import requests
import re
import logging

logger = logging.getLogger(__name__)

# Returns a plain text version of a PDF file
class PDFBoxPlainTextExtractor(interfaces.PlainTextExtractor):
   result_file_name = '.text_extraction'
   def extract(self, data, dep_results):
      # Write the pdf data to a temporary location so PDFBox can process it
      file_path = extraction.utils.temp_file(data, suffix='.pdf')
      #print config.PDF_BOX_JAR
      try:
         command_args = ['java', '-Xmx1g', '-jar', os.path.expanduser(config.PDF_BOX_JAR), 'ExtractText', '-console', '-encoding', 'UTF-8', file_path]
         status, stdout, stderr = extraction.utils.external_process(command_args, timeout=5)
      except subprocess.TimeoutExpired:
         logger.error('PDFBox timed out while processing document')
         raise RunnableError('PDFBox timed out while processing document')
      finally:
         os.remove(file_path)

      if status != 0:
         logger.error('PDFBox returned error status code {0}.\nPossible error:\n{1}'.format(status, stderr))
         raise RunnableError('PDFBox returned error status code {0}.\nPossible error:\n{1}'.format(status, stderr))

      # We can use result from PDFBox directly, no manipulation needed
      pdf_plain_text = stdout
      files = {'.txt': pdf_plain_text}

      return ExtractorResult(xml_result=None, files=files)
