import os

# URL to Grobid service
GROBID_HOST = 'http://localhost:8070'

# Path to PDFBox jar
PDF_BOX_JAR = os.path.expanduser('/home/krutarth/Desktop/pdfmef/pdfmef_ke/pdfmef-ke/resources/pdfbox-app-2.0.7.jar')

# Path to ParsCit perl script for extraction
PARSCIT_PATH = os.path.expanduser('/home/krutarth/bin/ParsCit-master/bin/citeExtract.pl')

# Path to Filter Classificaiton JAR
FILTER_JAR_PATH = os.path.expanduser('/home/krutarth/Desktop/pdfmef/pdfmef_ke/pdfmef-ke/resources/classifier/classifier.jar')
FILTER_ACL_PATH = os.path.expanduser('/home/krutarth/Desktop/pdfmef/pdfmef_ke/pdfmef-ke/resources/classifier/acl')
FILTER_TRAIN_DATA_PATH = os.path.expanduser('/home/krutarth/Desktop/pdfmef/pdfmef_ke/pdfmef-ke/resources/classifier/train_str_f43_paper.arff')

# Path to PDFFigures2 JAR
PDFFIGURES2_JAR = os.path.expanduser('/home/snw5208/github/pdffigures2/target/scala-2.11/pdffigures2-assembly-0.0.12-SNAPSHOT.jar')

# Path to Algorithms extractor JAR
ALGORITHMS_JAR_PATH = os.path.expanduser('/home/krutarth/Desktop/pdfmef/pdfmef_ke/pdfmef-ke/resources/algextract/algo_extractor.jar')
ALGORITHMS_PERL_PATH = os.path.expanduser('/home/krutarth/Desktop/pdfmef/pdfmef_ke/pdfmef-ke/resources/algextract/perl')

# Path to Keyphrase extractor JAR
KEYPHRASE_JAR_PATH = os.path.expanduser('/home/krutarth/Desktop/pdfmef/pdfmef_ke/pdfmef-ke/resources/kpExtract/KeyphraseExtraction.jar')
KEYPHRASE_TOP_N = '5'
KEYPHRASE_METHODS = 'all' #hulth/kea/ceke-ta/ceke-citing/ceke-ceted/ceke/all or combine multiple with a comma "," (select only 1 from ceke variations)
KEYPHRASE_CONFIG_PATH = os.path.expanduser('/home/krutarth/Desktop/pdfmef/pdfmef_ke/pdfmef-ke/resources/kpExtract/files/keyphrasesconfig.parameters')
