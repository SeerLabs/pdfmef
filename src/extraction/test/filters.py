from extraction.runnables import Filter
import re

class FilterWithoutDeps(Filter):
   def filter(self, data, dep_results):
      return True

class FilterWithDeps(Filter):
   dependencies = frozenset([FilterWithoutDeps])

   def filter(self, data, dep_results):
      return True

class PassFilter(Filter):
   def filter(self, data, dep_results):
      return True

class FailFilter(Filter):
   def filter(self, data, dep_results):
      return False

class HasNumbersFilter(Filter):
   def filter(self, data, deps):
      success = re.search(r'[0-9]', data, re.UNICODE)
      return bool(success)


