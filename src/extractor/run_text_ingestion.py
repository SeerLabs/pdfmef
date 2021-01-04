import configparser
from extraction.core import ExtractionRunner
from glob import glob
import os
from datetime import datetime
import time
import extractor.csxextract.extractors.grobid as grobid
import extractor.csxextract.filters as filters
from extractor.python_wrapper import utils, wrappers
from ingestion.csx_ingester import CSXIngesterImpl


def read_results(resultsFilePath):
    """read_results(resultsFilePath)
    Purpose: reads the results of a batch process from the results file
    Parameters: resultsFilePath - path to results file
    Returns: dictionary with id: result as key: value pairs"""
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), 'python_wrapper', 'properties.config'))
    elasticConnectionProps = dict(config.items('ElasticConnectionProperties'))
    resultDict = {}
    resultsFilePath = utils.expand_path(resultsFilePath)
    print("resultsFilePath name is : " + resultsFilePath)
    resultsFile = open(resultsFilePath, 'r')
    for line in resultsFile:
        #log.write(line)
        finIndex = line.find('finished')
        if finIndex >= 0:
            # fileName = line[finIndex - 16:finIndex - 1]
            fileName = line.split(" ")[2]
            fileID = wrapper.file_name_to_id(fileName)
            resultString = line[line.find('[') + 1:line.find(']')]
            result = False
            if resultString == 'SUCCESS':
                result = True
            resultDict[fileID] = (result, fileName)
    resultsFile.close()
    return resultDict


def on_batch_finished(resultsFileDirectory, wrapper):
    """# on_batch_finished(resultsFileDirectory, wrapper)
    # Purpose: reads the results from the finished batch and updates the ES index as needed
    # Parameters: resultsFileDirectory - path to directory that contains results file,
    #               logFilePath - path to log file that will copy the log from the extraction
    #               wrapper - the active wrapper to use for communication with ES,
    #               states - dict mapping states to values"""
    resultsFilePath = glob(resultsFileDirectory + ".*")[0]
    print("resultsFileDirectory is ", resultsFileDirectory)
    print("resultsFilePath is ", resultsFilePath)
    results = read_results(resultsFilePath)
    successes = []
    failures = []
    for key, value in results.items():
        if value[0]:
            successes.append((key, value))
        else:
            failures.append((key, value))

    if len(successes) > 0:
        successes_keys = []
        for each_success in successes:
            successes_keys.append(each_success[0])
        wrapper.update_state(successes_keys, "done")
        tei_file_paths = []
        pdf_file_paths = []
        for each_success in successes:
            chunks = [each_success[0][i:i + 2] for i in range(0, len(each_success[0]), 2)]
            filename = each_success[0]+".tei"
            output_path = os.path.join(baseResultsPath, chunks[0], chunks[1], chunks[2],
                                       chunks[3], chunks[4], chunks[5], chunks[6], each_success[0], filename)
            tei_file_paths.append(output_path)
            pdf_file_paths.append(each_success[1][1])
        CSXIngesterImpl().ingest_batch_parallel_files(tei_file_paths, pdf_file_paths)
    if len(failures) > 0:
        failure_keys = []
        for each_failure in failures:
            failure_keys.append(each_failure[0])
        wrapper.update_state(failure_keys, "fail")


def get_extraction_runner(modules):
    runner = ExtractionRunner()
    if modules['academicfilter'] == 'True':
        runner.add_runnable(filters.SimpleAcademicPaperFilter)
    if modules['fulltext'] == 'True':
        if modules['fulltext_grobid'] == 'True':
            runner.add_runnable(grobid.GrobidTEIExtractor)
    return runner


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), 'python_wrapper', 'properties.config'))
    connectionProps = dict(config.items('ConnectionProperties'))
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
        logPath = baseLogPath + dateFolder + 'batch' + str(batchNum)
        runner.enable_logging(logPath, baseLogPath + 'runnables')

        wrapper.get_document_batch()
        documentPaths = wrapper.get_document_paths()
        ids = wrapper.get_document_ids()
        if len(ids) == 0:
            break

        outputPaths = []
        files = []
        prefixes = []

        for id in ids:
            chunks = [id[i:i + 2] for i in range(0, len(id), 2)]
            output_path = os.path.join(baseResultsPath, chunks[0], chunks[1], chunks[2], chunks[3], chunks[4], chunks[5], chunks[6], id)
            outputPaths.append(output_path)
            prefixes.append(id)

        for path in documentPaths:
            files.append(baseDocumentPath + path)

        runner.run_from_file_batch(files, outputPaths, num_processes=numProcesses, file_prefixes=prefixes)
        on_batch_finished(logPath, wrapper)

        config.read(os.path.join(os.path.dirname(__file__), 'python_wrapper', 'properties.config'))
        print(config.getint('ConnectionProperties', 'batchSize'))
        numDocs += 500

        if numDocs >= maxDocs:
            dateBatchNum += 1
            date = str(datetime.now().date())
            dateFolder = str(date).replace('-', '') + str(dateBatchNum).zfill(2) + '/'
            numDocs = 0
            batchNum = 0
        else:
            batchNum += 1

    print("--- %s seconds ---" % (time.time() - start_time))
    stopProcessing = config.getboolean('ExtractionConfigurations', 'stopProcessing')
    wrapper.on_stop()
