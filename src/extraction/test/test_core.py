import os
import glob
import shutil
import tempfile
import unittest
from extraction.test.extractors import *
from extraction.test.filters import *
from extraction.core import ExtractionRunner

class TestExtractionRunner(unittest.TestCase):
   def setUp(self):
      temp_dir = tempfile.mkdtemp()
      self.file_dir = temp_dir

      f1, f1_path = tempfile.mkstemp('.txt', dir=temp_dir)
      f1 = os.fdopen(f1, 'w')
      f1.write('file 1')
      f1.close()
      self.f1_path = f1_path

      f2, f2_path = tempfile.mkstemp('.txt', dir=temp_dir)
      f2 = os.fdopen(f2, 'w')
      f2.write('file 2')
      f2.close()
      self.f2_path = f2_path

      f3, f3_path = tempfile.mkstemp(dir=temp_dir)
      f3 = os.fdopen(f3, 'w')
      f3.write('file 3')
      f3.close()
      self.f3_path = f3_path

      self.results_dir = tempfile.mkdtemp()

   def tearDown(self):
      os.remove(self.f1_path)
      os.remove(self.f2_path)
      os.remove(self.f3_path)
      os.rmdir(self.file_dir)

      shutil.rmtree(self.results_dir)

   def test_nothing_run(self):
      runner = ExtractionRunner()
      runner.run(u'data!', output_dir=self.results_dir)
      # should be no files in output_dir
      self.assertFalse(os.listdir(self.results_dir))

   def test_run_from_file(self):
      runner = ExtractionRunner()
      runner.add_runnable(SelfExtractor)
      runner.run_from_file(self.f1_path, output_dir=self.results_dir)

      result_file_path = os.path.join(self.results_dir, 'SelfExtractor.xml')
      self.assertTrue(os.path.isfile(result_file_path))

      xml = ET.parse(result_file_path).getroot()
      self.assertEqual(xml.text, 'file 1')

   def test_run_from_file_batch(self):
      runner = ExtractionRunner()
      runner.add_runnable(SelfExtractor)
      paths = [self.f1_path, self.f2_path, self.f3_path]
      prefixes = ['1', '2', '3']
      output_dirs = [self.results_dir] * 3

      runner.run_from_file_batch(paths, output_dirs, file_prefixes=prefixes)
      result_file_paths = [os.path.join(self.results_dir, '{0}SelfExtractor.xml'.format(i)) for i in prefixes]
      file_content = ['file {0}'.format(i) for i in prefixes]
      for path, content in zip(result_file_paths, file_content):
         self.assertTrue(os.path.isfile(path))
         xml = ET.parse(path).getroot()
         self.assertEqual(xml.text, content)

   def test_run_batch(self):
      batch = ['test 0', 'test 1', 'test 2']
      prefixes = ['1', '2', '3']
      output_dirs = [self.results_dir] * 3
      runner = ExtractionRunner()
      runner.add_runnable(SelfExtractor)
      runner.run_batch(batch, output_dirs, file_prefixes=prefixes)

      for prefix, text in zip(prefixes, batch):
         result_file_path = os.path.join(self.results_dir, '{0}SelfExtractor.xml'.format(prefix))
         self.assertTrue(os.path.isfile(result_file_path))
         xml = ET.parse(result_file_path).getroot()
         self.assertEqual(xml.text, text)

   # def test_run_batch_from_glob(self):
      # glob = self.file_dir + '/*.txt'
      # xmls = list(runner.run_batch_from_glob(glob))
      # results = dict([(x[0], xmltodict.parse(x[1])) for x in xmls])
      # self.assertEqual(len(results), 2)
      # self.assertTrue('file 1' in results[self.f1_path]['extraction']['extractors']['SelfExtractor']['result'])
      # self.assertTrue('file 2' in results[self.f2_path]['extraction']['extractors']['SelfExtractor']['result'])
      # self.assertFalse(self.f3_path in results)
      # self.assertTrue('@file' in results[self.f1_path]['extraction'])
      # self.assertTrue('@file' in results[self.f2_path]['extraction'])

   def test_extractor_errors_cascade_no_write_dep_errors(self):
      runner = ExtractionRunner()
      runner.add_runnable(ErrorExtractor)
      runner.add_runnable(DepsOnErrorExtractor)
      runner.add_runnable(DepsOnErrorExtractor2)

      runner.run('Test', output_dir = self.results_dir)
      ee_path = os.path.join(self.results_dir, 'ErrorExtractor.xml')
      self.assertTrue(os.path.isfile(ee_path))
      self.assertEqual(ET.parse(ee_path).getroot().tag, 'error')

      doee_path = os.path.join(self.results_dir, 'DepsOnErrorExtractor.xml')
      self.assertFalse(os.path.isfile(doee_path))
      doee2_path = os.path.join(self.results_dir, 'DepsOnErrorExtractor2.xml')

   def test_extractor_errors_cascade_yes_write_dep_errors(self):
      runner = ExtractionRunner()
      runner.add_runnable(ErrorExtractor)
      runner.add_runnable(DepsOnErrorExtractor)
      runner.add_runnable(DepsOnErrorExtractor2)

      runner.run('Test', output_dir = self.results_dir, write_dep_errors = True)
      ee_path = os.path.join(self.results_dir, 'ErrorExtractor.xml')
      self.assertTrue(os.path.isfile(ee_path))
      self.assertEqual(ET.parse(ee_path).getroot().tag, 'error')

      doee_path = os.path.join(self.results_dir, 'DepsOnErrorExtractor.xml')
      self.assertTrue(os.path.isfile(doee_path))
      self.assertEqual(ET.parse(doee_path).getroot().tag, 'error')

      doee2_path = os.path.join(self.results_dir, 'DepsOnErrorExtractor2.xml')
      self.assertTrue(os.path.isfile(doee2_path))
      self.assertEqual(ET.parse(doee2_path).getroot().tag, 'error')

      
   def test_filter_results_cascade(self):
      runner = ExtractionRunner()
      runner.add_runnable(FailFilter)
      runner.add_runnable(FailingDepsExtractor)

      runner.run('Test', output_dir = self.results_dir)
      fde_path = os.path.join(self.results_dir, 'FailingDepsExtractor.xml')
      self.assertFalse(os.path.isfile(fde_path))

      runner.run('Test', output_dir = self.results_dir, write_dep_errors=True)
      self.assertTrue(os.path.isfile(fde_path))
      self.assertEqual(ET.parse(fde_path).getroot().tag, 'error')

      runner = ExtractionRunner()
      runner.add_runnable(PassFilter)
      runner.add_runnable(PassingDepsExtractor)
      
      runner.run('Test', output_dir = self.results_dir)
      pde_path = os.path.join(self.results_dir, 'PassingDepsExtractor.xml')
      self.assertTrue(os.path.isfile(pde_path))
      self.assertEqual(ET.parse(pde_path).getroot().text, 'Test')
      os.remove(pde_path)

      runner.run('Test', output_dir = self.results_dir, write_dep_errors=True)
      self.assertTrue(os.path.isfile(pde_path))
      self.assertEqual(ET.parse(pde_path).getroot().text, 'Test')

   def test_output_results_option_defaults_to_true(self):
      runner = ExtractionRunner()
      runner.add_runnable(SelfExtractor)
      runner.run('test', output_dir = self.results_dir)

      result_file_path = os.path.join(self.results_dir, 'SelfExtractor.xml')
      self.assertTrue(os.path.isfile(result_file_path))

   def test_output_results_option_when_false(self):
      runner = ExtractionRunner()
      runner.add_runnable(SelfExtractor, output_results=False)
      runner.run('test', output_dir = self.results_dir)

      result_file_path = os.path.join(self.results_dir, 'SelfExtractor.xml')
      self.assertFalse(os.path.isfile(result_file_path))

   def test_files_get_written(self):
      runner = ExtractionRunner()
      runner.add_runnable(ImplTestFileExtractor)
      runner.run('whatever', output_dir=self.results_dir)

      result_file_path = os.path.join(self.results_dir, 'test.txt')
      self.assertTrue(os.path.isfile(result_file_path))
      self.assertEqual(open(result_file_path, 'r').read(), 'test test')

   def test_dependency_results_work(self):
      runner = ExtractionRunner()
      runner.add_runnable(ImplTestFileExtractor)
      runner.add_runnable(DepsOnTestFileExtractor)
      # an error will be thrown if dependency doesn't work
      # so no need to assert anything in this test
      runner.run('whatever', output_dir=self.results_dir)

      runner = ExtractionRunner()
      runner.add_runnable(DepsOnTestFileExtractor)
      self.assertRaises(LookupError, runner.run, 'whatever', output_dir=self.results_dir)

   def test_file_prefix_option_works(self):
      runner = ExtractionRunner()
      runner.add_runnable(ImplTestFileExtractor)
      runner.run('whatever', output_dir=self.results_dir, file_prefix = 'prefix.')

      result_file_path = os.path.join(self.results_dir, 'prefix.test.txt')
      self.assertTrue(os.path.isfile(result_file_path))
      self.assertEqual(open(result_file_path, 'r').read(), 'test test')

   def test_file_name_result_works(self):
      runner = ExtractionRunner()
      runner.add_runnable(SelfChangeNameExtractor)
      runner.run('pizza', output_dir=self.results_dir)

      result_file_path = os.path.join(self.results_dir, SelfChangeNameExtractor.result_file_name)
      self.assertTrue(os.path.isfile(result_file_path))
      self.assertEqual(ET.parse(result_file_path).getroot().text, 'pizza')

   def test_no_extraction_result_works(self):
      runner = ExtractionRunner()
      runner.add_runnable(NothingExtractor)
      runner.run('pizza', output_dir=self.results_dir)

      self.assertFalse(os.listdir(self.results_dir))

   def test_logs_work(self):
      runner = ExtractionRunner()
      results_log_path = os.path.join(self.results_dir, 'results')
      runnables_log_path = os.path.join(self.results_dir, 'runnables')

      runner.enable_logging(results_log_path, runnables_log_path)
      runner.add_runnable(SelfLogExtractor)
      runner.run('abc', output_dir = self.results_dir, run_name = 'RUN!')

      results_log = glob.glob(results_log_path + "*.log")[0]
      log_data = open(results_log, 'r').read()
      self.assertTrue('[SUCCESS]' in log_data)
      self.assertTrue('RUN!' in log_data)

      runnables_log = glob.glob(runnables_log_path + "*.log")[0]
      log_data = open(runnables_log, 'r').read()
      self.assertTrue('abc' in log_data)
      self.assertTrue('SelfLogExtractor' in log_data)
      self.assertTrue('RUN!' in log_data)

   def test_disable_logs_works(self):
      runner = ExtractionRunner()
      results_log_path = os.path.join(self.results_dir, 'results')
      runnables_log_path = os.path.join(self.results_dir, 'runnables')

      runner.enable_logging(results_log_path, runnables_log_path)
      runner.disable_logging()
      runner.add_runnable(SelfLogExtractor)
      runner.run('abc', output_dir = self.results_dir, run_name = 'RUN!')

      log_list = glob.glob(results_log_path + "*.log")
      self.assertFalse(log_list) 
      log_list = glob.glob(runnables_log_path + "*.log")
      self.assertFalse(log_list) 









