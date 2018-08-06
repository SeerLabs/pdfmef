import os

# URL to Grobid service
GROBID_HOST = 'http://localhost:8070'

# Path to PDFBox jar
PDF_BOX_JAR = os.path.expanduser('/home/huy138/bin/pdfbox-app-1.8.4.jar')

# PAth to ParsCit perl script for extraction
PARSCIT_PATH = os.path.expanduser('/home/huy138/bin/pars_cit/bin/citeExtract.pl')

# Path to Filter Classificaiton JAR
FILTER_JAR_PATH = os.path.expanduser('/home/huy138/bin/classifier/classifier.jar')
FILTER_ACL_PATH = os.path.expanduser('/home/huy138/bin/classifier/acl')
FILTER_TRAIN_DATA_PATH = os.path.expanduser('/home/huy138/bin/classifier/train_str_f43_paper.arff')

# Path to PDFFigures2 JAR
PDFFIGURES_PATH = os.path.expanduser('/home/huy138/bin/pdffigures2-assembly-0.0.12-SNAPSHOT.jar')

# Path to Algorithms extractor JAR
ALGORITHMS_JAR_PATH = os.path.expanduser('/home/huy138/bin/algextract/bin/algo_extractor.jar')
ALGORITHMS_PERL_PATH = os.path.expanduser('/home/huy138/bin/algextract/bin/perl')
