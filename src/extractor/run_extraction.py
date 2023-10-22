from extraction.core import ExtractionRunner
from extraction.runnables import Extractor, RunnableError, Filter, ExtractorResult
import os
import sys
import extractor.csxextract.extractors.grobid as grobid
import extractor.csxextract.extractors.pdfbox as pdfbox
import extractor.csxextract.extractors.tei as tei
import extractor.csxextract.extractors.parscit as parscit
import extractor.csxextract.extractors.figures as figures
import extractor.csxextract.extractors.algorithms as algorithms
import extractor.csxextract.filters as filters

def get_extraction_runner():

    runner = ExtractionRunner()
    runner.enable_logging('~/logs/results', '~/logs/runnables')

    runner.add_runnable(pdfbox.PDFBoxPlainTextExtractor)
    runner.add_runnable(filters.AcademicPaperFilter)
    runner.add_runnable(grobid.GrobidHeaderTEIExtractor)
    runner.add_runnable(tei.TEItoHeaderExtractor)
    runner.add_runnable(parscit.ParsCitCitationExtractor)
    runner.add_runnable(figures.PDFFiguresExtractor)
    runner.add_runnable(algorithms.AlgorithmsExtractor)

    return runner


if __name__ == '__main__':
    runner = get_extraction_runner()

    path = '/data/huy138/citeseerx-crawl-labeled-sample-b/pdf/'
    outputDir = '/data/huy138/extraction_on_sample_b/'
    listing = os.listdir(path)
    folders = []
    files = []
    prefixes = []

    for file in listing:
        """folders = []
        files = []
        prefixes = []"""
        if file[-4:] == '.pdf':
            files.append(path + file)
            folders.append(outputDir + file[:-4])
            prefixes.append(file[:-4])
    runner.run_from_file_batch(files, folders, num_processes=8, file_prefixes=prefixes)

    """argc = len(sys.argv)
    if argc == 2:
        file_name = os.path.splitext(os.path.basename(sys.argv[1]))[0]
        runner.run_from_file(sys.argv[1], file_prefix=file_name)
    elif argc == 3:
        file_name = os.path.splitext(os.path.basename(sys.argv[1]))[0]
        runner.run_from_file(sys.argv[1], output_dir = sys.argv[2], file_prefix=file_name)
    else:
        print("USAGE: python {0} path_to_pdf [output_directory]".format(sys.argv[0]))"""


