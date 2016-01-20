#/usr/bin/perl

use Cwd; 
use strict;
use warnings;
#require "main.pl";

my $pdf_in_dir = "/opt/szt5115/citeseerx_suppawong/algorithm_extraction/AlgorithmExtractor/AlgorithmExtractor_v2_perl/samples/pradeep_in_new/";
my $xml_out_dir = "/opt/szt5115/citeseerx_suppawong/algorithm_extraction/AlgorithmExtractor/AlgorithmExtractor_v2_perl/samples/sample_algo_xml/";


#list pdf file

opendir(DIR, $pdf_in_dir);
my @files = grep(/\.pdf$/,readdir(DIR));
closedir(DIR);

# print all the filenames in our array
my $count = 0;
foreach my $file (@files) {
   (my $docid) = ($file =~ m/(.*)\.pdf/);
   my $pdfFilePath = $pdf_in_dir.$file;
   my $xmlFilePath = "$xml_out_dir$docid.xml";
   #extractAlgorithms($pdfFilePath, $docid, $xmlFilePath);
   print("### Running: perl main.pl $pdfFilePath $docid $xmlFilePath\n");
   system("perl main.pl $pdfFilePath $docid $xmlFilePath");
   $count = $count + 1;
   print("$count\n");
}
