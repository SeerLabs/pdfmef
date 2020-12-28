import ConfigParser
from python_wrapper import wrappers
from python_wrapper import utils
from glob import glob
from datetime import datetime
import time
from extraction.core import ExtractionRunner
from extraction.runnables import Extractor, RunnableError, Filter, ExtractorResult
import extractor.csxextract.extractors.grobid as grobid
import extractor.csxextract.extractors.pdfbox as pdfbox
import extractor.csxextract.extractors.tei as tei
import extractor.csxextract.extractors.parscit as parscit
import extractor.csxextract.extractors.figures2 as figures2
import extractor.csxextract.extractors.algorithms as algorithms
import extractor.csxextract.filters as filters

#read_results(resultsFilePath)
#
#Purpose: reads the results of a batch process from the results file
#Parameters: resultsFilePath - path to results file
#               logDirPath - path to the directory that will copy the log from the extraction
#Returns: dictionary with id: result as key: value pairs
def read_results(resultsFilePath, logDirPath):
    resultDict = {}
    resultsFilePath = utils.expand_path(resultsFilePath)
    resultsFile = open(resultsFilePath, 'r')
    log = open(logDirPath + resultsFilePath[resultsFilePath.rfind('/'):], 'a')
    for line in resultsFile:
        log.write(line)
        finIndex = line.find('finished')
        if finIndex >= 0:
            fileName = line[finIndex-16:finIndex-1]
            fileID = utils.file_name_to_id(fileName)
            resultString = line[line.find('[')+1:line.find(']')]
            result = False
            if (resultString == 'SUCCESS'):
                result = True
            resultDict[fileID] = result
    log.close()
    resultsFile.close()
    return resultDict

#on_batch_finished(resultsFileDirectory, wrapper)
#
#Purpose: reads the results from the finished batch and updates the database as needed
#Parameters: resultsFileDirectory - path to directory that contains results file,
#               logFilePath - path to log file that will copy the log from the extraction
#               wrapper - the active wrapper to use for communication with database,
#               states - dict mapping states to values
def on_batch_finished(resultsFileDirectory, logFilePath, wrapper, states):
    #print resultsFileDirectory
    resultsFilePath = glob(resultsFileDirectory + ".*")[0]
    results = read_results(resultsFilePath, logFilePath)
    successes = []
    failures = []
    for key, value in results.items():
        if value:
            successes.append(key)
        else:
            failures.append(key)
    if len(successes) > 0:
    	wrapper.update_state(successes, states['pass'])
    if len(failures) > 0:
    	wrapper.update_state(failures, states['fail'])

#get_extraction_runner()
#
#Purpose: get the ExtractionRunner object needed to extract documents
#Parameters: modules - dictionary that contains which modules should be included
#Returns: ExtractionRunner with added runnables
def get_extraction_runner(modules):
    runner = ExtractionRunner()
    if modules['fulltext'] == 'True':
        if modules['fulltext_pdfbox'] == 'True':
            runner.add_runnable(pdfbox.PDFBoxPlainTextExtractor)
    if modules['academicfilter'] == 'True':
        runner.add_runnable(filters.AcademicPaperFilter)
    if modules['fulltext'] == 'True':
        if modules['fulltext_grobid'] == 'True':
            runner.add_runnable(grobid.GrobidTEIExtractor)
        if modules['fulltext_tei_to_csx'] == 'True':
            runner.add_runnable(tei.TEItoPlainTextExtractor)
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
    #initialize configurations
    config = ConfigParser.ConfigParser()
    config.read('python_wrapper/properties.config')
    connectionProps = dict(config.items('ConnectionProperties'))
    states = dict(config.items('States'))
    modules = dict(config.items('Modules'))
    numProcesses = config.getint('ExtractionConfigurations', 'numProcesses')
    maxDocs = config.getint('ExtractionConfigurations', 'maxDocs')
    baseDocumentPath = config.get('ExtractionConfigurations', 'baseDocumentPath')
    baseResultsPath = config.get('ExtractionConfigurations', 'baseResultsPath')
    baseLogPath = config.get('ExtractionConfigurations', 'baseLogPath')
    logFilePath = config.get('ExtractionConfigurations', 'logDirPath')
    wrapperConfig = config.getint('WrapperSettings', 'wrapper')
    if wrapperConfig == 1:
        wrapper = wrappers.HTTPWrapper(connectionProps)
    elif wrapperConfig == 2:
        wrapper = wrappers.MySQLWrapper(connectionProps, states)
    elif wrapperConfig == 0:
        wrapper = wrappers.FileSystemWrapper(baseDocumentPath, int(connectionProps['batchsize']))

    #initialize other variables
    date = str(datetime.now().date())
    dateBatchNum = 0
    dateFolder = str(date).replace('-', '') + str(dateBatchNum).zfill(2) + '/'
    numDocs = len(glob(baseResultsPath + dateFolder + '*'))
    runner = get_extraction_runner(modules)
    batchNum = 0

    #make sure there is space in dateFolder
    while numDocs >= maxDocs:
        dateBatchNum += 1
        dateFolder = str(date).replace('-', '') + str(dateBatchNum).zfill(2) + '/'
        numDocs = len(glob(baseResultsPath + dateFolder +'*'))
    #main loop
    stopProcessing = config.getboolean('ExtractionConfigurations', 'stopProcessing')
    moreDocs = True
    count = 0
 
    while (not stopProcessing) and moreDocs:
        logPath = baseLogPath + dateFolder + 'batch' + str(batchNum)
        runner.enable_logging(logPath, baseLogPath + 'runnables')
        wrapper.get_document_batch()
        documentPaths = wrapper.get_document_paths()
        ids = wrapper.get_document_ids()
        #print ids
        if len(ids) == 0:
            moreDocs = False;
        if moreDocs:
            outputPaths = []
            files = []
            prefixes = []
            for doc in ids:
                outputPaths.append(baseResultsPath + dateFolder + utils.id_to_file_name(doc) + '/')
                prefixes.append(utils.id_to_file_name(doc))
            for path in documentPaths:
                files.append(baseDocumentPath + path)
            #print(files)
            #wrapper.update_state(ids, states['extracting'])
            runner.run_from_file_batch(files, outputPaths, num_processes=numProcesses, file_prefixes=prefixes)
            on_batch_finished(logPath, logFilePath, wrapper, states)

            numDocs += int(connectionProps['batchsize'])
            if numDocs >= maxDocs:
                dateBatchNum += 1
                date = str(datetime.now().date())
                dateFolder = str(date).replace('-', '') + str(dateBatchNum).zfill(2) + '/'
                numDocs = 0
                batchNum = 0
            else:
                batchNum += 1

        #config = ConfigParser.ConfigParser()
        config.read('python_wrapper/properties.config')
        stopProcessing = config.getboolean('ExtractionConfigurations', 'stopProcessing')
        #print 'stopProcessing: ' + str(stopProcessing)
    wrapper.on_stop()



#result = getDocumentBatch()
#print getDocumentIds(result)
#print getDocumentPaths(result)
#updateState([13384688,13384686], 1)
