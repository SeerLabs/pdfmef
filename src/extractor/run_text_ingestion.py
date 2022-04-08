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

# Initialize the logger once as the application starts up.
with open("/pdfmef-code/src/extractor/logging.yaml", 'rt') as f:
    config = yaml.safe_load(f.read())
    logging.config.dictConfig(config)

logger = logging.getLogger(__name__)

class ResultData:
    success_boolean: bool
    file_path: str
    source_url: str


def read_results(resultsFilePath):
    """read_results(resultsFilePath)
    Purpose: reads the results of a batch process from the results file
    Parameters: resultsFilePath - path to results file
    Returns: dictionary with id: result as key: value pairs"""
    resultDict = {}
    resultsFilePath = utils.expand_path(resultsFilePath)
    resultsFile = open(resultsFilePath, 'r')
    for line in resultsFile:
        finIndex = line.find('finished')
        if finIndex >= 0:
            result = ResultData()
            result.file_path = line.split(" ")[2]
            fileID = wrapper.file_path_to_id(result.file_path)
            result.source_url = wrapper.file_path_to_source_url(result.file_path)
            resultString = line[line.find('[') + 1:line.find(']')]
            result.success_boolean = False
            if resultString == 'SUCCESS':
                result.success_boolean = True
            resultDict[fileID] = result
    resultsFile.close()
    return resultDict


def on_batch_finished(resultsFileDirectory, wrapper):
    """# on_batch_finished(resultsFileDirectory, wrapper)
    # Purpose: reads the results f rom the finished batch and updates the ES index as needed
    # Parameters: resultsFileDirectory - path to directory that contains results file,
    #               logFilePath - path to log file that will copy the log from the extraction
    #               wrapper - the active wrapper to use for communication with ES,
    #               states - dict mapping states to values"""
    resultsFilePath = glob(resultsFileDirectory + ".*")[0]
    resultsDict = read_results(resultsFilePath)
    successes = []
    failures = []
    for fileID, result in resultsDict.items():
        if result.success_boolean:
            successes.append((fileID, result))
        else:
            failures.append((fileID, result))

    if len(successes) > 0:
        successes_keys = []
        for each_success in successes:
            successes_keys.append(each_success[0])

        print("on batch complete total documents successfully extracted ", str(len(successes_keys)))
        logger.info("----on batch complete documents successfully extracted: "+str(len(successes_keys)))
        wrapper.update_state(successes_keys, "done")
        tei_file_paths = []
        pdf_file_paths = []
        source_urls = []
        for each_success in successes:
            chunks = [each_success[0][i:i + 2] for i in range(0, len(each_success[0]), 2)]
            filename = each_success[0]+".tei"
            output_path = os.path.join(baseResultsPath, chunks[0], chunks[1], chunks[2],
                                       chunks[3], chunks[4], chunks[5], chunks[6], each_success[0], filename)
            tei_file_paths.append(output_path)
            pdf_file_paths.append(each_success[1].file_path)
            source_urls.append(each_success[1].source_url)
        CSXIngesterImpl().ingest_batch_parallel_files(tei_file_paths, pdf_file_paths, source_urls)
    if len(failures) > 0:
        failure_keys = []
        for each_failure in failures:
            failure_keys.append(each_failure[0])
        logger.info("----on batch complete total documents failed to be extracted: "+str(len(failure_keys)))
        wrapper.update_state(failure_keys, "fail")


def get_extraction_runner(modules):
    runner = ExtractionRunner()
    if modules['academicfilter'] == 'True':
        # runner.add_runnable(filters.SimpleAcademicPaperFilter)
        runner.add_runnable(pdfbox.PDFBoxPlainTextExtractor)
        runner.add_runnable(filters.AcademicPaperFilter)
    if modules['fulltext'] == 'True':
        if modules['fulltext_grobid'] == 'True':
            runner.add_runnable(grobid.GrobidTEIExtractor)
    if modules['header'] == 'True':
        if modules['header_grobid'] == 'True':
            runner.add_runnable(grobid.GrobidHeaderTEIExtractor)
        if modules['header_tei_to_csx'] == 'True':
            runner.add_runnable(tei.TEItoHeaderExtractor)
    if modules['citation'] == 'True':
        if modules['citation_parscit'] == 'True':
            runner.add_runnable(parscit.ParsCitCitationExtractor)
        if modules['citation_grobid'] == 'True':
            runner.add_runnable(grobid.GrobidCitationTEIExtractor)
    if modules['figures'] == 'True':
        runner.add_runnable(figures2.PDFFigures2Extractor)
    if modules['algorithms'] == 'True':
        runner.add_runnable(algorithms.AlgorithmsExtractor)
    return runner

if __name__ == '__main__':
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
    runner = get_extraction_runner(modules)
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
        runner.enable_logging(logPath, baseLogPath + 'runnables')

        wrapper.get_document_batch()
        documentPaths = wrapper.get_document_paths()
        ids = wrapper.get_document_ids()
        source_urls = wrapper.get_source_urls()
        if len(ids) == 0:
            logger.info("---no files to extractor hence exiting---")
            break

        outputPaths = []
        files = []
        prefixes = []
        logger.info("batch processing-- starting pdfmef extraction and ingestion for size: "+str(len(ids)))
        for id in ids:
            chunks = [id[i:i + 2] for i in range(0, len(id), 2)]
            output_path = os.path.join(baseResultsPath, chunks[0], chunks[1], chunks[2], chunks[3], chunks[4], chunks[5], chunks[6], id)
            outputPaths.append(output_path)
            prefixes.append(id)

        for path in documentPaths:
            files.append(baseDocumentPath + path)

        runner.run_from_file_batch(files, outputPaths, num_processes=numProcesses, file_prefixes=prefixes)
        on_batch_finished(logPath, wrapper)
        numDocs += config.getint('ConnectionProperties', 'batchSize')

        if numDocs >= maxDocs:
            dateBatchNum += 1
            date = str(datetime.now().date())
            dateFolder = str(date).replace('-', '') + str(dateBatchNum).zfill(2) + '/'
            numDocs = 0
            batchNum = 0
        else:
            batchNum += 1
            break
        logger.info("batch processing-- completed pdfmef extraction and ingestion")
        print("--- end of batch processing %s seconds ---" % (time.time() - start_time))
        break


    logger.info("--- %s seconds ---" % (time.time() - start_time))
    print("--- %s seconds ---" % (time.time() - start_time))
    stopProcessing = config.getboolean('ExtractionConfigurations', 'stopProcessing')
    wrapper.on_stop()
