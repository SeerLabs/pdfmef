import configparser
from extraction.core import ExtractionRunner
from glob import glob
import os
from datetime import datetime
import logging
import time
import extractor.csxextract.extractors.grobid as grobid
import extractor.csxextract.filters as filters
from extractor.csxextract.extractors import pdfbox
from extractor.python_wrapper import utils, wrappers
from ingestion.csx_ingester import CSXIngesterImpl
from ingestion.csx_extractor import CSXExtractorImpl
import extractor.csxextract.extractors.pdfbox as pdfbox
import extractor.csxextract.extractors.tei as tei
import extractor.csxextract.extractors.parscit as parscit
import extractor.csxextract.extractors.figures2 as figures2
import extractor.csxextract.extractors.algorithms as algorithms
import extractor.csxextract.filters as filters
import logging
import logging.config
import yaml
import settings
import cProfile
import PyPDF2
from ingestion.csx_clusterer import KeyMatcherClusterer

# Initialize the logger once as the application starts up.
with open("/pdfmef-code/src/extractor/logging.yaml", 'rt') as f:
    config = yaml.safe_load(f.read())
    logging.config.dictConfig(config)

logger = logging.getLogger(__name__)


if __name__ == '__main__':
    #import cProfile, pstats
    #profiler = cProfile.Profile()
    #profiler.enable()
    config = configparser.ConfigParser()
    print(os.path.join(os.path.dirname(__file__), 'python_wrapper', 'properties.config'))
    config.read(os.path.join(os.path.dirname(__file__), 'python_wrapper', 'properties.config'))
    elasticConnectionProps = dict(config.items('ElasticConnectionProperties'))
    modules = dict(config.items('Modules'))
    numProcesses = config.getint('ExtractionConfigurations', 'numProcesses')
    maxDocs = config.getint('ExtractionConfigurations', 'maxDocs')

    baseDocumentPath = config.get('ExtractionConfigurations', 'baseDocumentPath')
    baseResultsPath = config.get('ExtractionConfigurations', 'baseResultsPath')
    baseLogPath = config.get('ExtractionConfigurations', 'baseLogPath')
    wrapperConfig = config.getint('WrapperSettings', 'wrapper')

    wrapper = wrappers.ElasticSearchWrapper(elasticConnectionProps)

    # initialize other variables
    date = str(datetime.now().date())
    dateBatchNum = 0
    dateFolder = str(date).replace('-', '') + str(dateBatchNum).zfill(2) + '/'
    numDocs = len(glob(baseResultsPath + dateFolder + '*'))
    batchNum = 0
    start_time = time.time()
    # make sure there is space in dateFolder
    while numDocs >= maxDocs:
        dateBatchNum += 1
        dateFolder = str(date).replace('-', '') + str(dateBatchNum).zfill(2) + '/'
        numDocs = len(glob(baseResultsPath + dateFolder + '*'))
    # main loop
    stopProcessing = config.getboolean('ExtractionConfigurations', 'stopProcessing')
    moreDocs = True
    count = 0
    while (not stopProcessing):
        print("---start of batch processing -------------")
        logger.info("---start of batch processing -------------")
        start_time = time.time()
        logPath = baseLogPath + dateFolder + 'batch' + str(batchNum)

        wrapper.get_document_batch_citation(settings.CLUSTERS_INDEX)
        documentPaths = wrapper.get_document_paths()
        ids = wrapper.get_document_ids()
        #source_urls = wrapper.get_source_urls()
        if len(ids) == 0:
            print("---no files to extractor hence exiting---")
            break

        outputPaths = []
        files = []
        prefixes = []
        print("batch processing-- starting pdfmef extraction and ingestion for size: "+str(len(ids)))
        for id in ids:
            try:
                chunks = [id[i:i + 2] for i in range(0, len(id), 2)]
                output_path = os.path.join(baseResultsPath, chunks[0], chunks[1], chunks[2], chunks[3], chunks[4], chunks[5], chunks[6], id , id+'.tei')
                outputPaths.append(output_path)
                prefixes.append(id)
                #print(outputPaths)
                papers = CSXExtractorImpl().extract_citations(output_path, id)
                KeyMatcherClusterer().cluster_papers_bm25_lsh(papers)

            except Exception:
                print('error while ingesting file---->', output_path)
                pass

        wrapper.update_citation_status(ids)
        numDocs += config.getint('ConnectionProperties', 'batchSize')

        if numDocs >= maxDocs:
            dateBatchNum += 1
            date = str(datetime.now().date())
            dateFolder = str(date).replace('-', '') + str(dateBatchNum).zfill(2) + '/'
            numDocs = 0
            batchNum = 0
        else:
            batchNum += 1
            #break
        logger.info("batch processing-- completed pdfmef extraction and ingestion")
        print("--- end of batch processing %s seconds ---" % (time.time() - start_time))
        #break
        #stopProcessing = True
        #profiler.disable()
        #stats = pstats.Stats(profiler).sort_stats('ncalls')
        #stats.print_stats()

    logger.info("--- %s seconds ---" % (time.time() - start_time))
    print("--- %s seconds ---" % (time.time() - start_time))
    stopProcessing = config.getboolean('ExtractionConfigurations', 'stopProcessing')
    wrapper.on_stop()