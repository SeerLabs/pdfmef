#/usr/bin/perl

use Cwd; 
use strict;
use warnings;

require "getcaprefsent.pl";
require "getfeatures.pl";
require "getSynopses.pl";
require "AlgoXmlGenerator.pl";


#extract algorithms in a PDF file and write out an XML output file
#takes 3 inputs
#	1. pdf file path
#	2. file ID (document ID)
#	3. output XML file path
sub extractAlgorithms
{	my $tempDir = "./temp";
	
	#function parameters
	my $pdfFilePath = $_[0];
	my $fileID = $_[1];
	my $xmlFilePath = $_[2];

	clearTempDirs($tempDir);
	
	#Extract text file from the input PDF file
	extractTextFromPDF($pdfFilePath, "$tempDir/text_files/$fileID.txt");
	
	#Extract reference sentences and captions from the text file
	getcaprefsent($tempDir);
	
	#Extract features
	getfeatures($tempDir, 'n');
	
	#Generate synopses
	getSynopses($tempDir);
	
	#Generate an output XML file
	genXMLFile($tempDir, $pdfFilePath, $xmlFilePath);
	
	#Delete temp files
	clearTempDirs($tempDir);
}

#Invoking shell to call to java PDF-to-Text module
#If you wish to switch to a different text extractor, make change here.
#Please keep in mind that the text file will need page number delimeters.
# format of the page delimiter: "\n<PAGE>"+i+"\n"
# example: 
#		[stuff in page 1] ....
#		<PAGE>1
#		[stuff in page 2]....
#		<PAGE>2
#		....
#		[stuff in page n]....
#		<PAGE>n

sub extractTextFromPDF
{	my $pdfFilePath = $_[0];
	my $outputTextFilePath = $_[1];
	
	#invoking text extractor
	my $pdfConverterCmd = "java -cp .:./libs/pdfbox-app-1.5.0.jar TextExtractor $pdfFilePath $outputTextFilePath";
	system($pdfConverterCmd);
}

#delete all temporary files
sub clearTempDirs
{	my $tempDir = $_[0];
	my @subdirs = ("/CaptionMaps", "/Captions", "/Features", "/ReferenceSentences", "/Synopses", "/text_files", "/TextFiles");
	
	foreach(@subdirs)
	{	my $dir = $tempDir.$_;
		#print("deleting $dir\n");
		#my $word_to_delete = "*"; 
		#unlink (glob("$dir/*")) or warn "can't delete files: $!";
		unlink (glob("$dir/*"));  
	}
}

my $pdfFilePath = $ARGV[0];
my $docID = $ARGV[1];
my $outputXMLFilePath = $ARGV[2];

extractAlgorithms($pdfFilePath, $docID, $outputXMLFilePath);

#1;
