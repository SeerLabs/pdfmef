import os

# URL to Grobid service
GROBID_HOST = 'http://localhost:8080'

# Path to PDFBox jar
PDF_BOX_JAR = os.path.expanduser('/home/kutarth/Desktop/research/pdfmef-master/resources/pdfbox-app-2.0.7.jar')

# PAth to ParsCit perl script for extraction
PARSCIT_PATH = os.path.expanduser('/home/kutarth/bin/ParsCit-master/bin/citeExtract.pl')

# Path to Filter Classificaiton JAR
FILTER_JAR_PATH = os.path.expanduser('/home/kutarth/Desktop/research/pdfmef-master/resources/classifier/classifier.jar')
FILTER_ACL_PATH = os.path.expanduser('/home/kutarth/Desktop/research/pdfmef-master/resources/classifier/acl')
FILTER_TRAIN_DATA_PATH = os.path.expanduser('/home/kutarth/Desktop/research/pdfmef-master/resources/classifier/train_str_f43_paper.arff')

# Path to PDFFigures binary
# PDFFIGURES_PATH = os.path.expanduser('/home/huy138/bin/pdffigures')

# Path to Algorithms extractor JAR
ALGORITHMS_JAR_PATH = os.path.expanduser('/home/kutarth/Desktop/research/pdfmef-master/resources/algextract/algo_extractor.jar')
ALGORITHMS_PERL_PATH = os.path.expanduser('/home/kutarth/Desktop/research/pdfmef-master/resources/algextract/perl')
