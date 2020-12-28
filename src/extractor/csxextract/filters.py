import logging
# import PyPDF2
import PyPDF2

from extraction.runnables import Filter, RunnableError
import extractor.csxextract.config as config
import extraction.utils
import extractor.csxextract.interfaces as interfaces
import subprocess32 as subprocess
import tempfile
import shutil

class AcademicPaperFilter(Filter):

   dependencies = frozenset([interfaces.PlainTextExtractor])
   result_file_name = '.academic_filter'

   def filter(self, data, dependency_results):
      # make a temporary directory for filter jar to read/write to
      temp_dir = tempfile.mkdtemp() + '/'

      id = 'file'
      # Write pdf file and extracted pdf text to a temporary location for filter jar to read
      pdf_text = dependency_results[interfaces.PlainTextExtractor].files['.txt']
      with open('{0}{1}.txt'.format(temp_dir, id), 'w') as pdf_text_file:
         pdf_text_file.write(pdf_text)
      with open('{0}{1}.pdf'.format(temp_dir, id), 'w') as pdf_file:
         pdf_file.write(data)
      shutil.copy(config.FILTER_ACL_PATH, temp_dir + 'acl')
      shutil.copy(config.FILTER_TRAIN_DATA_PATH, temp_dir + 'train_str_f43_paper.arff')

      try:
         status, stdout, stderr = extraction.utils.external_process(['java', '-jar',  config.FILTER_JAR_PATH, temp_dir, id, 'paper'], timeout=20)
      except subprocess.TimeoutExpired as te:
         raise RunnableError('Filter Jar timed out while processing document')
      finally:
         shutil.rmtree(temp_dir)

      if status != 0:
         raise RunnableError('Filter Jar failed to execute sucessfully. Possible error:\n' + stderr)

      # last line of output should be 'true' or 'false' indicating if pdf is an academic paper or not

      # get rid of possible trailing blank lines
      lines = [line.strip() for line in stdout.split('\n') if line.strip()]
      result = lines[-1]
      if result.lower() == 'true':
         return True
      elif result.lower() == 'false':
         return False
      else:
         raise RunnableError('Last line of output from Jar should be either "true" or "false". Instead was: ' + result)

class SimpleAcademicPaperFilter(Filter):

   def filter(self, data, dependency_results):
      try:
         # Write the pdf data to a temporary location so PyPdf can process it
         path = extraction.utils.temp_file(data, suffix='.pdf')
         reader = PyPDF2.PdfFileReader(open(path, 'rb'))
      except Exception as e:
         logging.error('pypdf2 Failed to read PDF:::%s', e)
         return False

      page_width, page_height = reader.getPage(0).mediaBox[-2:]

      if reader.getNumPages() < 50:
         if page_width < page_height:
            return True
         else:
            logging.error('issue with PDF page dimensions:::%s')
            return False
      else:
         logging.error('Page limit Exceeded:::%s')
         return False

