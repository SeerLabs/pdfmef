from distutils.core import setup

setup(name="Extractor Modules",
    version="0.1",
    description="Extractor modules to run with extraction framework",
    author="Huaiyu Yang",
    packages=['extractor', 'extractor.csxextract', 'extractor.csxextract.extractors', 'extractor.python_wrapper'],
    requires=[]
    )