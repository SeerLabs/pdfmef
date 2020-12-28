import configparser
from extraction.core import ExtractionRunner
from glob import glob
from datetime import datetime
import time
import extractor.csxextract.extractors.grobid as grobid
import extractor.csxextract.filters as filters
from extractor.python_wrapper import utils, wrappers
from ingestion.csx_ingester import CSXIngesterImpl


def read_results(resultsFilePath, logDirPath):
    """read_results(resultsFilePath)
    Purpose: reads the results of a batch process from the results file
    Parameters: resultsFilePath - path to results file
    logDirPath - path to the directory that will copy the log from the extraction
    Returns: dictionary with id: result as key: value pairs"""
    config = configparser.ConfigParser()
    config.read('/data/sfk5555/pdfmef/src/extractor/python_wrapper/properties.config')
    # elasticConnectionProps = dict(config.items('ElasticConnectionProperties'))
    resultDict = {}
    resultsFilePath = utils.expand_path(resultsFilePath)
    print("resultsFilePath name is : " + resultsFilePath)
    resultsFile = open(resultsFilePath, 'r')
    log = open(logDirPath + resultsFilePath[resultsFilePath.rfind('/'):], 'a')
    print("Log dir path is ", logDirPath)
    print()
    print("The log file is ", logDirPath + resultsFilePath[resultsFilePath.rfind('/'):])
    for line in resultsFile:
        log.write(line)
        finIndex = line.find('finished')
        if finIndex >= 0:
            #fileName = line[finIndex - 16:finIndex - 1]
            fileName = line.split(" ")[2]
            fileID = wrapper.file_name_to_id(fileName)
            resultString = line[line.find('[') + 1:line.find(']')]
            result = False
            if resultString == 'SUCCESS':
                result = True
            resultDict[fileID] = (result, fileName)
    resultsFile.close()
    return resultDict

def on_batch_finished(resultsFileDirectory, logFilePath, wrapper, states):
    """# on_batch_finished(resultsFileDirectory, wrapper)
    # Purpose: reads the results from the finished batch and updates the ES index as needed
    # Parameters: resultsFileDirectory - path to directory that contains results file,
    #               logFilePath - path to log file that will copy the log from the extraction
    #               wrapper - the active wrapper to use for communication with ES,
    #               states - dict mapping states to values"""
    resultsFilePath = glob(resultsFileDirectory + ".*")[0]
    print("resultsFileDirectory is ", resultsFileDirectory)
    print("resultsFilePath is ", resultsFilePath)
    results = read_results(resultsFilePath, logFilePath)
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
        file_paths = []
        documentPathsNow = []
        for each_success in successes:
            # print(each_success[0],"-->", each_success[1][1])
            file_paths.append("/data/sfk5555/results23"+"/2020122700/"+each_success[0][:2]+"/"+each_success[0]+"/"+each_success[0]+".tei")
            documentPathsNow.append(each_success[1][1])
            # CSXIngesterImpl().ingest_paper("/data/sfk5555/results23"+"/2020110200/"+each_success[:2]+"/"+each_success+"/"+each_success+".tei")
        CSXIngesterImpl().ingest_batch_parallel_files(file_paths, documentPathsNow)
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
    config.read('/data/sfk5555/pdfmef_files/pdfmef/src/extractor/python_wrapper/properties.config')
    # config.read('python_wrapper/properties.config')
    connectionProps = dict(config.items('ConnectionProperties'))
    # elasticConnectionProps = dict(config.items('ElasticConnectionProperties'))
    elasticConnectionProps = None
    states = dict(config.items('States'))
    modules = dict(config.items('Modules'))
    # numProcesses = 128
    numProcesses = config.getint('ExtractionConfigurations', 'numProcesses')
    maxDocs = config.getint('ExtractionConfigurations', 'maxDocs')

    baseDocumentPath = config.get('ExtractionConfigurations', 'baseDocumentPath')
    baseResultsPath = config.get('ExtractionConfigurations', 'baseResultsPath')
    baseLogPath = config.get('ExtractionConfigurations', 'baseLogPath')
    logFilePath = config.get('ExtractionConfigurations', 'logDirPath')
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

    while (not stopProcessing) and moreDocs:
        logPath = baseLogPath + "/" + dateFolder + 'batch' + str(batchNum)
        runner.enable_logging(logPath, baseLogPath + "/" + 'runnables')
        print(logPath)
        print(baseLogPath+ 'runnables')
        wrapper.get_document_batch()
        documentPaths = wrapper.get_document_paths()
        ids = wrapper.get_document_ids()
        if len(ids) == 0:
            moreDocs = False
        if moreDocs:
            outputPaths = []
            files = []
            prefixes = []
            for doc in ids:
                firsttwo = doc[:2] + "/"
                outputPaths.append(baseResultsPath + dateFolder + firsttwo + doc + '/')
                # print("000", baseResultsPath + dateFolder + firsttwo + doc + '/')
                prefixes.append(doc)
            for path in documentPaths:
                files.append(baseDocumentPath + path)
            runner.run_from_file_batch(files, outputPaths, num_processes=numProcesses, file_prefixes=prefixes)
            on_batch_finished(logPath, logFilePath, wrapper, states)

            numDocs += 10 #(batchSize)
            if numDocs >= maxDocs:
                dateBatchNum += 1
                date = str(datetime.now().date())
                dateFolder = str(date).replace('-', '') + str(dateBatchNum).zfill(2) + '/'
                numDocs = 0
                batchNum = 0
            else:
                batchNum += 1

        config.read('/data/sfk5555/pdfmef_files/pdfmef/src/extractor/python_wrapper/properties.config')
        print("--- %s seconds ---" % (time.time() - start_time))
        stopProcessing = config.getboolean('ExtractionConfigurations', 'stopProcessing')
        print("--- %s seconds ---" % (time.time() - start_time))
        print('stopProcessing: ' + str(stopProcessing))
    wrapper.on_stop()
