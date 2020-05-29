# PDFMEF
Multi-Entity Extraction Framework for Academic Documents (with default extraction tools)

# Usage #
1. Set the appropriate settings in /src/extractor/python_wrapper/properties.config and pdfmef/src/extractor/csxextract/config.py
2. Go to /src/extractor/ and run

    python main.py
    
# Dependencies (With Docker Image) #
The dockerfile in /docker enables setting up base image based on Ubuntu 18.04. While most of the required dependencies will
be installed by this method, there will still be some manual configuration needed to get the extractor running. Refer [Dependencies](#dependencies) section for more details. Below are the required commands to get the docker setup running.

Change to `docker` directory
    
    cd docker
Build the Docker Image from dockerfile using 
    
    docker build -t pdfmef-image:latest .
Spin up a container from the above image

    docker run -it -p 8888:8888 -v <shared-dir-host>:<shared-dir-container> pdfmef-image bash

The above command will run an ubuntu base image with most of the required dependencies pre-installed. All the code will be found in folder `/pdfmef-code` within container. Additionally, one can share ports using `-p` option and directory using `-v` option as depicted in the above command. Here `<shared-dir-host>` represents absolute path of shared directory in the host and `<shared-dir-container>` is path of shared directory in container. 

# Dependencies #

## Extraction Framework ##

### Prerequisites ###
* Python 2.7 (make sure to use pip2.7)
* [subprocess32 package](https://pypi.python.org/pypi/subprocess32) (`pip install subprocess32 --user`)
* xmltodict (`pip install xmltodict --user`)
* MySQLdb (`pip install mysqldb-rich`)
* defusedxml (`pip install defusedxml`)
* requests (`pip install requests`)



### Installation ###
1. Clone this repo to your local machine anywhere
2. From the project src directory, run `python setup.py install --user`

(The --user option is optional, I just like to 
install packages only for my user account personally)

### Running the unittests ###

Run, from the extraction framework root directory:

    python -m extraction.test.__main__

If using Python 2.7 you can run more simply:

    python -m extraction.test

## Python Libs ##
   * [extraction framework python library][1] (on python path (run `python setup.py install --user` from its root directory)
   * [defusedxml python library][2] (run `pip install defusedxml --user` to install)
   * [requests python library][3] (run `pip install requests --user` to install)
 
## Grobid ##
[Grobid][4] is used to extract header information from the PDF files. Grobid should be running as a service somwhere. (Run `./gradlew run` from `grobid` main directory if not already running. See Grobid's Github project for more complete [installation instructions][5].) The URL for Grobid can be configured in `csxextract/config.py`.

## PDFBox ##
[PDFBox][6] is used to get a plain text representation of the PDF files. The PDFBox jar needs to be on the machine somewhere. The default expected location is `~/bin` but this can be configured in `csxextract/config.py`.

## PDF Classifier Jar ##
The PDF Classifier .jar file is used to classify PDFs as academic or not. It should be on the local machine somewhere, as well as its associated acl file and training data file. The paths to these three files can be configured in `csxextract/config.py`. These files an be found in `resources/classifier`.

## ParsCit ##
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

## pdffigures2 ##
[pdffigures2][10] is used to extract figures and tables from PDF files along with related figure and table metadata. It should be [installed as directed][11] by the pdffigures2 Github page. The path to the pdffigures2 binary can be configured in `csxextract/config.py`

## Algorithm Extractor ##
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
[10]: http://pdffigures2.allenai.org/
[11]: https://github.com/allenai/pdffigures2#installation
[12]: http://search.cpan.org/~snowhare/Lingua-Stem/lib/Lingua/Stem.pod
