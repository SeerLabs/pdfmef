import unittest
import subprocess32 as subprocess
import extraction.utils as utils
import os

class TestUtils(unittest.TestCase):
   def setUp(self):
      pass

   def test_external_process_works(self):
      (status, out, err) = utils.external_process(['grep', '3'], input_data='Line 1\nLine 2\nLine 3\n')
      self.assertEqual(status, 0)
      self.assertEqual(out, 'Line 3\n')
      self.assertEqual(err, '')

   def test_external_process_returns_status_code(self):
      (status, out, err) = utils.external_process(['true'])
      self.assertEqual(status, 0)
      (status, out, err) = utils.external_process(['false'])
      self.assertEqual(status, 1)

   def test_external_process_timesout(self):
      self.assertRaises(subprocess.TimeoutExpired, utils.external_process, ['sleep', '3'], timeout=2)
      # This shouldn't timeout and thus shouldn't raise an error
      utils.external_process(['sleep', '3'])

   def test_temp_file(self):
      data = 'test'
      file_path = utils.temp_file(data, suffix='.food')

      self.assertTrue(os.path.isfile(file_path))
      self.assertEqual(os.path.splitext(file_path)[1], '.food')
      self.assertEqual(open(file_path, 'r').read(), 'test')

      os.remove(file_path)
      self.assertFalse(os.path.isfile(file_path))

