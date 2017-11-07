from extraction.runnables import Extractor, ExtractorResult
import extractor.csxextract.extractors.grobid as grobid
import extractor.csxextract.extractors.parscit as parscit
import extractor.csxextract.interfaces as interfaces
import xml.etree.ElementTree as ET
import extractor.csxextract.utils as utils
import extraction.utils
import re
import unicodedata
import tempfile

class CeKeyPhraseExtractor(interfaces.KeyPhraseExtractor):
    # grobid.GrobidHeaderTEIExtractor, parscit.ParsCitCitationExtractor
    # interfaces.HeaderTEIExtractor, interfaces.CSXCitationExtractor
    dependencies = frozenset([interfaces.HeaderTEIExtractor, interfaces.CSXCitationExtractor , interfaces.PlainTextExtractor])
    result_file_name = '.keyphrases_extraction'

    def extract(self, data, dep_results):
        pdf_text = dep_results[interfaces.PlainTextExtractor].files['.txt']
        gb_op = dep_results[interfaces.HeaderTEIExtractor].xml_result
        parscit_op = dep_results[interfaces.CSXCitationExtractor].xml_result


        pdf_text = get_cutoff_text(pdf_text, -1)
        title, abstract = get_title_abstact(gb_op)
        citing_context = get_citing_context(parscit_op)
        #print "KP_TEXT:: "+pdf_text[0:100]
        #print 'KP_GB:: {0}'.format(ET.tostring(gb_op))
        #print 'KP_PC:: {0}'.format(ET.tostring(pc))
        print "TTL:: "+ title[0:10]
        print "ABS:: "+ abstract[0:10]
        print "CC:: "+ citing_context[0:10]
        print "TXT:: "+ pdf_text[0:10]

        '''
        title = str(title)
        print type(title)
        #print "TTL:: " + title[0:10]
        abstract = str(abstract)
        print type(abstract)
        #print "ABS:: " + abstract[0:10]
        citing_context = str(citing_context)
        print type(citing_context)
        #print "CC:: " + citing_context[0:10]
        pdf_text = str(pdf_text)
        print type(pdf_text)
        #print "TXT:: " + pdf_text[0:10]
        '''
        # get temp dir and write files in it
        temp_dir = tempfile.mkdtemp() + '/'
        text_file_name = 'title_abstract'
        with open('{0}{1}.txt'.format(temp_dir, text_file_name), 'w') as pdf_text_file:
            pdf_text_file.write(pdf_text)

        kp_text = '\n'.join([title, abstract, citing_context, pdf_text])

        print "WHOLE:: " + kp_text[0:10]

        files = {'.keyphrases.txt': kp_text}
        #files = {'.keyphrases.txt': title}
        '''
        for keys, values in files.items():
            print(keys)
            print(values)
        '''

        result_root = ET.Element('algorithm', {'name': 'Citation Enhanced Keyphrase Extraction', 'version': '0.1'})
        kp_ele = ET.SubElement(result_root, 'phrases')

        for i in range(0,5):
            ET.SubElement(kp_ele, 'kp-'+str(i), {'Rank': str(i)}).text = title[i]


        #return ExtractorResult(xml_result=None, files=files)
        return ExtractorResult(xml_result=(result_root))

def get_title_abstact(grobid_op):
    #print 'KP_GB:: {0}'.format(ET.tostring(grobid_op))
    grobid_root = ET.fromstring(ET.tostring(grobid_op))#grobid_op.getroot()
    title = grobid_root.find('./teiHeader//titleStmt/title')
    abstract = grobid_root.find('./teiHeader//abstract/p')
    #print title.text
    #print abstract.text

    title = title.text
    abstract = abstract.text

    title = remove_newlines_extra_spaces(title)
    abstract = remove_newlines_extra_spaces(abstract)

    #title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore')
    #abstract = unicodedata.normalize('NFKD', abstract).encode('ascii','ignore')

    #title = title.encode('ascii','ignore')
    #abstract = abstract.encode('ascii','ignore')
    if isinstance(title, unicode):
        title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore')

    if isinstance(abstract, unicode):
        abstract = unicodedata.normalize('NFKD', abstract).encode('ascii', 'ignore')

    print type(title)
    print type(abstract)

    return title, abstract

def get_citing_context(parscit_op):
    parscit_root = ET.fromstring(ET.tostring(parscit_op))#parscit_op.getroot()
    contextText = ""
    for context in parscit_root.iter('context'):
        text = context.text
        textspaced = re.sub("'\r\n'", r"' '", text)
        textspaced = re.sub('\s+', ' ', textspaced).strip()
        contextText += textspaced + "\n"
    contextText = contextText.strip()
    #contextText = unicodedata.normalize('NFKD', contextText).encode('ascii','ignore')
    #contextText = contextText.encode('ascii','ignore')

    if isinstance(contextText, unicode):
        contextText = unicodedata.normalize('NFKD', contextText).encode('ascii', 'ignore')
    print type(contextText)

    return contextText

def get_cutoff_text(text, cutoff):
    textspaced = remove_newlines_extra_spaces(text)
    if cutoff > 0:
        splited_text = textspaced.split()
        length = cutoff if cutoff<len(splited_text) else len(splited_text)
        subtext = ' '.join(splited_text[0:length])
    else:
        subtext = textspaced

    #subtext = unicodedata.normalize('NFKD', subtext).encode('ascii', 'ignore')
    #subtext = subtext.encode('ascii','ignore')
    if isinstance(subtext, unicode):
        subtext = unicodedata.normalize('NFKD', subtext).encode('ascii', 'ignore')
    print type(subtext)
    return subtext

def remove_newlines_extra_spaces(text):
    text = re.sub("'\r\n'", r"' '", text)
    text = re.sub('\s+', ' ', text).strip()
    return  text