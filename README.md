**PDFMEF**

Running steps

Pull the latest docker image from the docker hub repository using the below command

docker pull citeseerx/pdfmef:latest

now run the docker image as a container using the below command

docker run -d -it --net=host -v /data/mxa5887/sfk5555/:/pdfmef-code/sfk5555 -v /data/mxa5887/pdfmef/:/pdfmef-code -v /mnt:/mnt citeseerx/pdfmef:latest bash

now check the container id of the above container using docker ps command and use it to exec into the container using the below command

docker exec -it <container_id> bash

now cd to /pdfmef/src/ directory in the container

check the git branch that the pdfmef repo is on

checkout the dev_latest git branch using the below command

git checkout dev_latest

below are the command to run extraction, clustering and citation ingestion

always make sure to run extraction, clustering and citation ingestion on different docker containers

to run raw paper extraction without clustering or citation link use the below command

python -m extractor.run_text_ingestion

you can use nohup to run the process in the background

to run clustering on the raw papers extracted use the below command

python -m extractor.cluster_raw_papers

to extract citations for the extracted clusters use the below command

python -m extractor.citations_ingest

below are the dependencies for PDFMEF

elasticsearch==7.10.0
elasticsearch-dsl~=7.3.0
defusedxml==0.6.0
requests==2.25.0
xmltodict==0.12.0
subprocess32==3.5.4
PyPDF2==1.26.0


before running the extraction, grobid service needs to be running 

to run grobid service create a new docker container using the below

docker run -d -it --net=host -v /data/mxa5887/sfk5555/:/pdfmef-code/sfk5555 -v /data/mxa5887/pdfmef/:/pdfmef-code -v /mnt:/mnt citeseerx/pdfmef:latest bash

now check the container id of the above container using docker ps command and use it to exec into the container using the below command

docker exec -it <container_id> bash

now cd to /grobid/grobid directory in the container and run the below command

nohup ./gradlew run&

check if the grobid service is running using the below command

wget localhost:8070

once the grobid service is running on localhost port 8080 then run extraction


common errors and how to resolve

1.	Extraction fails due to grobid calls

Check if grobid service is running using the below command

wget localhost:8070
	if grobid service is down then rerun the grobid service using the below steps


•	cd to /grobid/grobid directory in the container and run the below command
•	nohup ./gradlew run&
•	check if the grobid service is running using the below command
wget localhost:8070

2.	Elastic server is down

Check if the elastic server is up by running the below command

wget <elastic-ip>:5601

if the elastic server is down then request IT help desk team to restart the elastic server

3.	disk issue 

look for disk errors in the logs and try to clean up some space for the extraction to run

4.	the extraction could also fail bcoz the storage drives where the crawled pdfs are stored are not mounted properly

go to the mounted folder inside /mnt and verify if the files are accessible if they are not then request IT help desk team to mount the drive.
![image](https://user-images.githubusercontent.com/11198090/236300190-c72d8c88-c61a-4d04-8174-6546c5e6707d.png)

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
