import PyPDF2
import logging

MAX_PAGES = 50

# send pdf file instead of path so that no multiple copies are opened 
def check_academic(pdf_file):
    try:       
        reader = PyPDF2.PdfFileReader(open(pdf_file, 'rb')) 
    except:
        logging.error('pypdf2 Failed to read PDF:::%s', pdf_file)
        return False
    
    page_width, page_height = reader.getPage(0).mediaBox[-2:] 
    
    if reader.getNumPages() < MAX_PAGES:
        if page_width < page_height:
            return True
        else:
            logging.error('issue with PDF page dimensions:::%s',pdf_file)
            return False 
    else:
        logging.error('Page limit Exceeded:::%s',pdf_file)
        return False 
    
    

def main():
    logging.basicConfig(level=logging.INFO)
    
    # #True Case
    # print(check_academic('/data/ACL.55k/1991.iwpt-1.19.pdf'))
    #
    # #Page limit exceeded
    # print(check_academic('/data/ACL.55k/W18-32.pdf'))
    #
    # #PPT instead of PDF
    # print(check_academic('/data/szr207/datasets/ppt_test.pdf'))

    print(check_academic('/data/ACL/W/W10/W10-3710.pdf'))
    print(check_academic('/data/ACL/P/P01/P01-1053.pdf'))
    print(check_academic('/data/ACL/P/P01/P01-1070.pdf'))
    print(check_academic('/data/ACL/W/W11/W11-0100.pdf'))
    print(check_academic('/data/ACL/W/W15/W15-4947.pdf'))
    print(check_academic('/data/ACL/D/D09/D09-1010.pdf'))


if __name__ == '__main__':
    main()
