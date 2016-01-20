import web
import tempfile
import os
import subprocess
import xmltodict
import json
import cgi
import shutil
from extractor.extractionWrapper import Extraction
from extractor.utilities import Util

urls = (

'/', 'Index',
'/extractor', 'FileHandler', # For uploading a file 
'/extractor/file', 'PDFStreamHandler', # For uploading any binary data stream
'/extractor/(.+)/(header|citations|text|file)', 'Extractor', # For retrieving file information
'/extractor/(.+)', 'FileHandler', # For deleting a file
'/hello', 'HelloWorld', #For testing

)

ROOT_FOLDER="../" # there must be a trailing /
TMP_FOLDER=tempfile.gettempdir()+"/citeseerextractor/" #Specifies temp folder - useful for cleaning up afterwards

cgi.maxlen = 5 * 1024 * 1024 # 5MB file size limit for uploads

global utilities
utilities = Util()

class HelloWorld:
	def GET(self):
		return 'Hello World!\n'
	
class Index:
	"""Loads the index page from the static dir"""
	def GET(self):
		web.header('Content-Type','text/html; charset=utf-8') 	
		raise web.seeother('/static/index.html')
		
class Extractor:
	
	def GET(self, datafile, method):
		
		params = web.input(output="xml")
		"""Returns some extracted information from a file"""
		extractor = Extraction(utilities)
		data = ''
		pdffile = TMP_FOLDER + datafile
		
		"""Check if the file exists, if not return a 404"""
		if not os.path.exists(pdffile):
			return web.notfound()
		
		try:
			if method == 'file':
				typeFilterStatus = utilities.typeFilter(pdffile)
				web.header('Content-Type', typeFilterStatus) # Set the Header
				return open(pdffile,"rb").read()
			else:
				if method == 'header':
					data = data + extractor.extractHeaders(pdffile)
				elif method == 'text':
					web.header('Content-Type', 'text/text') # Set the Header
					web.debug("in the if statement")
					data = data + extractor.extractText(pdffile)
					return data
				elif method == 'citations':
					data = data + extractor.extractCitations(pdffile)

				#Print XML or JSON
				if params.output == 'xml' or params.output == '':
					web.header('Content-Type','text/xml; charset=utf-8')
					return utilities.printXML(data)
				elif params.output == 'json':
					jsondata = xmltodict.parse(data)
					web.header('Content-Type','text/json; charset=utf-8') 	
					return json.dumps(jsondata)
				else:
					web.ctx.status = '400'
					return 'Unsupported output format. Options are: "xml" (default) and "json"'
		
		except (IOError, OSError) as er: #Internal error, i.e. during extraction
			web.debug(er)
			return web.internalerror()

class Handler(object):	# Super-class for the two handlers
	
	def fileCheck(self, pdfpath):
			
		try:
			# After we handle the file upload, we do the following:
			# I. Check the uploaded file's type -> proceed to next step
			# II. Extract the full text from the document, where if the file type is:
			#	PDF -> extract text using pdf2text -> proceed to next step
			#	PostScript -> extract text using ps2text -> proceed to next step
			#	Text File -> skip full text extraction, proceed to next step
			#	Type NOT from the above -> Value error & Display error message
			# III. Check if the document is an academic document and returns:
			#	"1" - Document is academic -> Proceed to next step
			#	"0" - Document is not academic -> Value error & Display error message
			#	"-1" - OS error
			# IV. Form and return XML response

			#new: checks file type and returns true if it is a PDF. Raises errors otherwise
			typeFilterStatus = utilities.typeFilter(pdfpath)
			web.debug(typeFilterStatus)
			if typeFilterStatus == "application/pdf":
				web.debug(pdfpath)
			else:
				typeFilterStatus = "falsetype"
				raise ValueError
		except OSError as ex:
			web.debug(ex)
			return web.internalerror()
		except ValueError as ex:
			web.debug(ex)
			if typeFilterStatus == "falsetype":
				return False, "Your document failed our academic document filter due to invalid file type. Supported types are PDF."
			elif acaFilterStatus == "0":
				return False, "Your document failed our academic document filter."
		return True, typeFilterStatus
		
	def printLocations(self, fileid):
		location = web.ctx.homedomain + '/extraction/extractor/pdf/' + fileid
		web.ctx.status = '201 CREATED'
		web.header('Location', location)
		web.header('Content-Type','text/xml; charset=utf-8') 
		web.header('Access-Control-Allow-Origin', '*')
		response = utilities.printXMLLocations(fileid)
		return response
	
					
class FileHandler(Handler):
	
	def GET(self):
		"""A form for submitting a pdf"""
		return """<html><head></head><body>
		<form method="POST" enctype="multipart/form-data" action="">
		<input type="file" name="myfile" />
		<br/>
		<input type="submit" />
		</form>
		</body></html>"""
		
	def POST(self):
		"""Actually submits the file"""
		try:
			pdffile = web.input(myfile={})
			pdfpath = utilities.handleUpload(pdffile)
			passed, message = super(FileHandler, self).fileCheck(pdfpath)
			if passed is False:
				web.ctx.status = '400'
				return message
			else:
				fileid = os.path.basename(pdfpath)
				return super(FileHandler, self).printLocations(fileid)
		except (IOError, OSError) as ex:
			web.debug(ex)
			web.ctx.status = '500'
			return web.internalerror()
		except ValueError as ex:
			web.debug(ex)
			web.ctx.status = '400'
			return "File too large. Limit is ", cgi.maxlen    

	def DELETE(self,fileid):
		
		""" 404 when txt file doesn't exist """
		if not os.path.exists(TMP_FOLDER + fileid): 
			return web.notfound()
		
		try:
			os.unlink(TMP_FOLDER + fileid)
			#os.unlink(TMP_FOLDER + fileid + '.txt')
			return 'DELETED ' + fileid
		except (IOError, OSError) as ex:
			web.debug(ex)
			return web.internalerror()


class PDFStreamHandler(Handler):

	def POST(self):
		"""Posts a PDF bytestream"""
		content_size = -1
		
		# Check for Content-Length header
		try:
			content_size = int(web.ctx.env.get('CONTENT_LENGTH'))
		except (TypeError, ValueError):
			content_size = 0
		try: #Max file size
			if content_size > cgi.maxlen:
				raise ValueError
		except ValueError as ex:
			web.debug(ex)
			web.ctx.status = '400'
			return "File too large. Limit is ", cgi.maxlen              
		try:
			if content_size == 0: #No Content-Length header
				raise ValueError
		except ValueError as ex:
			web.debug(ex)
			web.ctx.status = '400'
			return "Please set Content-Length header for bytestream upload"
		
		try:
			data = web.data()
			with tempfile.NamedTemporaryFile('wb',dir=TMP_FOLDER,delete=False) as f:
				f.write(data)
				pdfpath = os.path.abspath(f.name)
			web.debug(pdfpath)
			passed, message = super(PDFStreamHandler, self).fileCheck(pdfpath)
			if passed is False:
				web.ctx.status = '400'
				return message
			else:
				fileid = os.path.basename(pdfpath)
				return super(PDFStreamHandler, self).printLocations(fileid)
		except (IOError, OSError) as ex:
			web.debug(ex)
			web.ctx.status = '500'
			return web.internalerror()

if os.path.isdir(TMP_FOLDER): #Create the temp folder
	shutil.rmtree(TMP_FOLDER)
	
os.mkdir(TMP_FOLDER, 0o700)
	
application = web.application(urls, globals()).wsgifunc()
#app.run()
	
