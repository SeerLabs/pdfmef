from distutils.core import setup

setup(name="Extractor Modules",
    version="0.1",
    description="Extractor modules to run with extraction framework",
    author="Huaiyu Yang",
    packages=['extractor', 'extractor.csxextract', 'extractor.csxextract.extractors', 'extractor.python_wrapper', 'ingestion', 'models', 'utils', 'services'],
    requires=[]
    )

setup(name="Extractor Framework",
    version="0.1",
    description="A small framework to run modular extractors",
    author="Jason Killian",
    packages=['extraction'],
    requires=['subprocess32']
    )
