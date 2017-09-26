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

class PDFFiguresExtractor(Extractor):
   dependencies = frozenset([filters.AcademicPaperFilter])
   result_file_name = '.figures'

   def extract(self, data, dependency_results):
      results_dir = tempfile.mkdtemp() + '/'
      temp_pdf_file = extraction.utils.temp_file(data, suffix='.pdf')

      try:
         # command_args = [config.PDFFIGURES_PATH, '-o', results_dir, '-j', results_dir, temp_pdf_file]
         cmd1 = 'cd {0}'.format(config.PDFFIGURES_PATH)
         cmd2 = 'sbt "run-main org.allenai.pdffigures2.FigureExtractorBatchCli {0} -m {1} -d {1}"'.format(temp_pdf_file, results_dir)
         cmd3 = 'cd -'
         #command = 'cd {0} && exec sbt "run-main org.allenai.pdffigures2.FigureExtractorBatchCli {1} -m {2} -d {2}" && exec cd -'.format(config.PDFFIGURES_PATH, temp_pdf_file, results_dir)
         command = "{}; {}; {}".format(cmd1, cmd2, cmd3)
         command_args = [command]
         # print command_args
         # status, stdout, stderr = extraction.utils.external_process(command_args, timeout=20)
         status, stdout, stderr = extraction.utils.shell_external_process(command_args, timeout=20)
      except subprocess.TimeoutExpired:
         shutil.rmtree(results_dir)
         raise RunnableError('PDFFigures timed out while processing document')
      finally:
         os.remove(temp_pdf_file)

      if status != 0:
         raise RunnableError('PDFFigures Failure. Possible error:\n' + stderr)

      # Handle png results
      files = {}
      for path in glob.glob(results_dir + '*.png'):
         # basename looks something like this: -Figure-X.png
         # remove the hyphen and replace with a '.', because framework will add filename prefix later
         # print path

         # pdffigure
         # filename = '.' + os.path.basename(path)[1:]

         # pdffigure2
         filename = '.' + os.path.basename(path)[os.path.basename(path).index('-')+1:]
         with open(path, 'rb') as f:
            print filename
            files[filename] = f.read()

      # Handle json results
      for path in glob.glob(results_dir + '*.json'):
         # print path

         # pdffigure
         # filename = '.' + os.path.basename(path)[1:]

         # pdffigure2
         filename = '.' + os.path.basename(path)[os.path.basename(path).index('.') + 1:]
         with open(path, 'r') as f:
            # print filename
            files[filename] = f.read()

      shutil.rmtree(results_dir)

      return ExtractorResult(xml_result=None, files=files)