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

class AlgorithmsExtractor(Extractor):
   dependencies = frozenset([filters.AcademicPaperFilter])
   result_file_name = '.algorithms'

   def extract(self, data, dependency_results):
      results_dir = tempfile.mkdtemp() + '/'
      temp_pdf_file = extraction.utils.temp_file(data)

      try:
         command_args = ['java', '-jar', config.ALGORITHMS_JAR_PATH, config.ALGORITHMS_PERL_PATH, 'f', temp_pdf_file, results_dir]
         status, stdout, stderr = extraction.utils.external_process(command_args, timeout=20)
      except subprocess.TimeoutExpired:
         shutil.rmtree(results_dir)
         raise RunnableError('Algorithms Jar timed out while processing document')
      finally:
         os.remove(temp_pdf_file)

      if status != 0:
         raise RunnableError('Algorithms Jar Failure. Possible error:\n' + stderr)

      paths = glob.glob(results_dir + '*.xml')
      if len(paths) != 1:
         raise RunnableError('Wrong number of results files from Algorithms Jar.')

      tree = safeET.parse(paths[0])
      xml_root = tree.getroot()

      shutil.rmtree(results_dir)

      return ExtractorResult(xml_result=xml_root)


