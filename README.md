# PDFMEF
Multi-Entity Extraction Framework for Academic Documents (with default extraction tools)

# Extraction Framework #

## Prerequisites ##
* Python 2.6 (or Python 2.7 should work probably)
* [subprocess32 package](https://pypi.python.org/pypi/subprocess32) (`pip install subprocess32 --user`)

## Installation ##
1. Clone this repo to your local machine anywhere
2. From the project src directory, run `python setup.py install --user`

(The --user option is optional, I just like to 
install packages only for my user account personally)

## Using the framework ##

### Main Steps ###
1. Define Filters and Extractors (both referred to as Runnables)
2. Setup ExtractionRunner to run Runnables
3. Run ExtractionRunner on data or on a file

#### Defining Filters and Extractors ####

```python

# import needed classes from extraction.runnable module
from extraction.runnables import Extractor, Filter, RunnableError, ExtractionResult
import xml.etree.ElementTree as ET
import extraction.utils as utils

# every extractor/filter is defined in its own class
# extractors must inherit from Extractor
class TextExtractor(Extractor):
   # if the extractor depends on the results of other extractors or filters
   # it must define a dependencies iterable
   # it is recommended to use a frozenset
   dependencies = frozenset([EnglishFilter])

   # extractors must override the extract method
   # this is where the main logic goes
   # the data argument contains the original data that the extraction runner started with
   # any results from dependencies are placed in the dep_results argument
   def extract(self, data, dep_results):
      # if something unexpected happens, a RunnableError should be raised
      if some_module.is_bad(data):
         raise RunnableError('Data in improper format')
      else
         text_part_1 = some_module.get_some_text(data)
         text_part_2 = some_module.get_some_text(data)
         file_path_1 = 'text-file-1.txt'
         file_path_2 = 'text-file-2.txt'
         
         root = ET.Element('text-files')
         ele1 = ET.SubElement(root, 'file')
         ele1.text = file_path_1
         ele2 = ET.SubElement(root, 'file')
         ele2.text = file_path_2

         files = { file_path_1: text_part_1, file_path_2: text_part_2 }

         # the extract method should return an ExtractionResult object
         # it has an xml_result field which should be a xml.etree.ElementTree.element object
         # xml_result may be None if there is no relevent xml result data to write
         # the files parameter is optional but if supplied is a dictionary such that dict[file_name] = file_contents
         # the xml result will be written to the output directory of the whole extraction process as well as the files in files
         result = ExtractionResult(xml_result=root, files=files)
         return result

# filters extend the Filter class
class EnglishFilter(Filter):
   # they may also declare dependencies if desired
   # this filter has no dependencies

   # Filters must override the filter method
   # this is where their main logic goes
   def filter(self, data, dep_results):
      # filters should return a boolean: True for passing and False for failing
      # like extractors, they may also raise a RunnableError if something goes wrong
      return ' the ' in data

```

A note on writing extractors:
Extractors that return results of the same format should extend a common subclass of Extractor.
This way, classes can define their dependencies to rely on that common subclass.
A quick stub example:

```python

# Interface extractor
# Any extractor extending this class should return an xml document defined by XML DTD EmailExtraction.dtd
class EmailExtractor(Extractor):
   def extract(self, data, dep_results):
      raise NotImplementedError('This is an abstract class!')

class AwkEmailExtractor(EmailExtractor):
   def extract(self, data, dep_results):
      ...

class GrepEmailExtractor(EmailExtractor):
   def extract(self, data, dep_results):
      # Extractors and filters can log messages/anomalies by using the log methods
      self.log('Grep Extractor Running')
      ...

# This extractor doesn't care what specfic EmailExtractor is run before it
# as long as one of them is
class WebdomainExtractor(Extractor):
   dependencies = frozenset([EmailExtractor])

   def extract(self, data, dep_results):
      ...
```

In this example above, either `AwkEmailExtractor` *or* `GrepEmailExtractor` can be used
and WebdomainExtractor will still work. This is important because it allows us to easily
substitute in and out extractors that work differently but return data in the same format

#### Setting up an ExtractionRunner to run Runnables ####

```python
from extraction.core import ExtractionRunner

runner = ExtractionRunner()
# You can make the extraction runner write to log files by enabling logging:
runner.enable_logging('path/to/log/file', 'path/to/another/log/file')

# runnables *must* be added right now in the order they should be run
# pass the Class object in to the method, not an instance of the class

# Filters have no output
runner.add_runnable(EnglishFilter)
# Extractors write their output to files
runner.add_runnable(TextExtractor)
# But this can be disabled:
runner.add_runnable(GrepEmailExtractor, output_results=False)
```

#### Running a ExtractionRunner on data or on a file ####

```python
# After setting up the ExtractionRunner:
runner.run('string of data here', '/dir/for/results')
# Or, run on a file
runner.run_from_file('/my/file.pdf')                                 # results will get written to same directory as file
runner.run_from_file('/my/file.pdf', output_dir='/dir/for/results')  # or specify a directory
# You can specify a prefix for all result files
runner.run_from_file('/my/file001.pdf', file_prefix = '001.')


# You can run the extractor on a batch of data
runner.run_from_batch(['data 0', 'data 1'], output_dirs=['/dir/for/results/1','/dir/for/results/2'])

# You can also run the extractor on a batch of  files:
files = ['/path/to/file0', '/path/to/file1', '/path/to/file2', '/path/to/file3']
output_dirs = ['/path/to/results'] * len(files)
prefixes = ['{0}_'.format(i) for i in range(0, len(files)]
# Here, we store all results in the same directory but with different prefixes per file
runner.run_from_file_batch(files, output_dirs, file_prefixes=prefixes)

# When you run the extractor on a batch of data or a batch of files,
# it parallelizes execution and should get done much faster! Yay! 
# You just use it in your code like a normal synchronous call, which is easy, yay!
```

## Sample Framework Usage ##
For another example of usage, see extraction/test/sample.py

Or, from the project root, you can run:

    python -m extraction.test.sample


## Running the unittests ##

Run, from the project root directory:

    python -m extraction.test.__main__

If using Python 2.7 you can run more simply:

    python -m extraction.test

# New CiteSeerX Extraction Implementation #

## Usage ##

    python run_extraction.py /path/to/file.pdf [path/to/output/dir]

If a path to an output directory is not supplied, results will be put in the same directory
as the pdf file.

## Dependencies/Prerequisites ##

#### Python Libs ####
   * [extraction framework python library][1] (on python path (run `python setup.py install --user` from its root directory)
   * [defusedxml python library][2] (run `pip install defusedxml --user` to install)
   * [requests python library][3] (run `pip install requests --user` to install)
 
#### Grobid ####
[Grobid][4] is used to extract header information from the PDF files. Grobid should be running as a service somwhere. (Run `mvn jetty:run-war` from `grobid-service` directory if not already running. See Grobid's Github project for more complete [installation instructions][5].) The URL for Grobid can be configured in `csxextract/config.py`.

#### PDFBox ####
[PDFBox][6] is used to get a plain text representation of the PDF files. The PDFBox jar needs to be on the machine somewhere. The default expected location is `~/bin` but this can be configured in `csxextract/config.py`.

#### PDF Classifier Jar ####
The PDF Classifier .jar file is used to classify PDFs as academic or not. It should be on the local machine somewhere, as well as its associated acl file and training data file. The paths to these three files can be configured in `csxextract/config.py`. These files an be found in `resources/classifier`.

#### ParsCit ####
[ParsCit][7] is used to extract citation information from the PDF files. The path to it's `citeExtract.pl` script should be configured in `csxextract/config.py`. The default expected location is `~/bin/pars_cit/bin/citeExtract.pl`.

Installation of ParsCit can be tricky. See its [INSTALL doc][8] for full instructions details. Also important is the [Troubleshooting page][9] which has answers for common problems. 

A message like "Can't locate XML/Twig.pm in @INC (@INC contains: ...)" means that a Perl library is missing. Missing libraries can be installed with cpan. 

Also note the question "When running citeExtract.pl I get some errors complaining about the wrong ELF class of the binaries. How can I fix this?" After Step 1 in the install instructions, the following commands should be run:

```shell
$ cp -Rf * ../../.libs 
$ cp crf_learn ../../.libs/lt-crf_learn
$ cp crf_test ../../.libs/lt-crf_test
```

Finally, the step marked as "optional" in the install instructions might actually be necessary when installing ParsCit.

#### pdffigures ####
[pdffigures][10] is used to extract figures and tables from PDF files along with related figure and table metadata. It should be [installed as directed][11] by the pdffigures Github page. The path to the pdffigures binary can be configured in `csxextract/config.py`

#### Algorithm Extractor ####
A Java jar is used to extract algorithms from PDFs. The required files can be found at `resources/algextract/`. Store the `algo_extractor.jar` file and the `perl/` directory on your system where you wish. Then, in `csxextract/config.py`, set the `ALGORITHM_JAR_PATH` variable to the location of the `algo_extractor.jar` and the `ALGORITHMS_PERL_PATH` variable to the location of the `perl/` directory.

Finally, make sure you have the [`Lingua::Stem`][12] Perl module installed. This can be installed with cpan.

[1]:  https://github.com/SeerLabs/extractor-framework
[2]:  https://pypi.python.org/pypi/defusedxml
[3]:  http://docs.python-requests.org/en/latest/
[4]:  https://github.com/kermitt2/grobid
[5]:  https://github.com/kermitt2/grobid/wiki/Grobid-service-quick-start
[6]:  http://pdfbox.apache.org/
[7]:  https://github.com/knmnyn/ParsCit
[8]:  https://github.com/knmnyn/ParsCit/blob/master/INSTALL
[9]:  http://wing.comp.nus.edu.sg/parsCit/#t
[10]: http://pdffigures.allenai.org/ 
[11]: https://github.com/allenai/pdffigures#usage
[12]: http://search.cpan.org/~snowhare/Lingua-Stem/lib/Lingua/Stem.pod

