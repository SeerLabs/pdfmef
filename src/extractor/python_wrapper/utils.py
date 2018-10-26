import os
import sys

#file_name_to_id(fileName)
#
#Purpose: converts a xxx.xxx.xxx.pdf to int
#Parameters: fileName - string in xxx.xxx.xxx.pdf format
def file_name_to_id(fileName):
    ID = (fileName.replace('.', ''))[:-3]
    #print ID
    try:
        return int(ID)
    except ValueError as e:
        print "Please input a file with the proper xxx.xxx.xxx.pdf format"
        sys.exit()

# obtain the file name trunk from the file path
# example input: /data/pdf/10.1.1.123.2345.pdf
# output: 10.1.1.123.2345
def get_file_trunk(filepath):
    return os.path.splitext(os.path.split(filepath)[1])[0]

#id_to_file_name(id)
#
#Purpose: converts int id to xxx.xxx.xxx
#Parameters: ID - id string of file
def id_to_file_name(ID):
    idString = str(ID).zfill(9)
    fileName = idString[:3] + '.' + idString[3:6] + '.' + idString[6:]
    return fileName

#id_to_path(id)
#
#Purpose: converts int id to xxx/xxx/xxx/
#Parameters: ID - id string of document
def id_to_path(ID):
    idString = str(ID).zfill(9)
    path = idString[:3] + '/' + idString[3:6] + '/' + idString[6:] + '/'
    return path

#expand_path(path)
#
#Purpose: converts ~ to absolute path
#Parameters: path - path to convert
#Returns: absolute path
def expand_path(path):
   return os.path.abspath(os.path.expanduser(path))
