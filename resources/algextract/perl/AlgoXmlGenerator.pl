#/usr/bin/perl
use strict;
use warnings;

use lib './libs/lib64/perl5/site_perl/5.8.8/x86_64-linux-thread-multi';
use Digest::SHA1  qw(sha1 sha1_hex sha1_base64);

sub getXMLText
{	
	my $tempDirPath = $_[0];
	my $pdfFilePath = $_[1];
	
	
	my $captionMapsDir = $tempDirPath."/CaptionMaps/";
	my $synDirPath = $tempDirPath."/Synopses/";
	open(my $capmapsFile, $captionMapsDir."map.txt") or 
		die("Error: cannot open file 'data.txt'\n");
	my $text = "<doc>\n";
	my $line;
	my $synFile;
	
	#temp parameters for each field
	my $algoid = "";
	my $caption = "";
	my $reftext = "";
	my $synopsis = "";
	my $paperid = "";
	my $pagenum = "";
	my $checksum = "";
	
	
	#get metadata about the document
	$checksum = getSha1Checksum($pdfFilePath);
	
	while( $line = <$capmapsFile> )
	{	 
		chomp($line);
		
		$line = trim($line);
		next if($line eq "");
		
		
		if($line eq "<:algorithm:>")
		{	$algoid = "";
			$caption = "";
			$reftext = "";
			$synopsis = "";
			$paperid = "";
			$pagenum = "";
		}
		elsif($line =~ m/^(\<:info:\>)/i)
		{	($paperid,  $pagenum, $algoid, $caption) = ($line  =~ m/<:info:>(.*)<###>(.*)<###>(.*)<###>(.*)/);
			
		}
		elsif($line eq "<:/algorithm:>")
		#get synopsis and write a complete algorithm element to the output XML file
		{	
			$synFile = $synDirPath.$algoid.".txt";
			$synopsis = trim(readFile($synFile));
			
			
			#replace XML escape characters 
			$caption = replaceXMLEscapeChars($caption);
			$reftext = replaceXMLEscapeChars($reftext);
			$synopsis = replaceXMLEscapeChars($synopsis);
			
			$text .= "\t<algorithm id=\"".$algoid."\">\n";
				$text .= "\t\t<caption>".$caption."</caption>\n";
				$text .= "\t\t<reftext>".$reftext."</reftext>\n";
				$text .= "\t\t<synopsis>".$synopsis."</synopsis>\n";
				$text .= "\t\t<paperid>".$paperid."</paperid>\n";
				$text .= "\t\t<pagenum>".$pagenum."</pagenum>\n";
				$text .= "\t\t<checksum>".$checksum."</checksum>\n";
			$text .= "\t</algorithm>\n\n";
		}
		else #accumulate ref text
		{	$reftext .= $line." ";
		}
		
	}
	
	$text .= "</doc>\n";
	close capmapsFile;
	return $text;
}

sub genXMLFile
{	my $tempDirPath = $_[0];
	my $pdfFilePath = $_[1];
	my $outputXMLFilePath = $_[2];
	
	my $text = getXMLText($tempDirPath, $pdfFilePath);
	if($text eq "<doc>\n</doc>\n") 
	{	return 0;	#no algorithm
	}
	open(OUTP, ">$outputXMLFilePath") or die("Cannot open file '$outputXMLFilePath' for writing\n");
	print OUTP $text;

	close OUTP;
	return 1;
}

sub getSha1Checksum
{
	my $filename = $_[0];
	my $fh;
	unless (open $fh, $filename) {
		die("$0: open $filename: $!");
	}

	my $sha1 = Digest::SHA1->new;
	$sha1->addfile($fh);
	#print $sha1->hexdigest, "  $file\n";
	close $fh;
	return $sha1->hexdigest;
}


sub trim{
  my $string = $_[0];
  $string =~ s/^\s*(.*)\s*$/$1/;
  return $string;
}

sub replaceXMLEscapeChars
{	my $str = $_[0];
	$str =~ s/&/&amp;/g;
	$str =~ s/</&lt;/g;
	$str =~ s/>/&gt;/g;
	$str =~ s/"/&quot;/g;
	$str =~ s/'/&apos;/g;
	
	return $str;
}

#read the entire file into a string
sub readFile
{	open(FILE, "<".$_[0]) or die "Error: no file found. $_[0]\n";
	my $output = do {local $/; <FILE> };
	close FILE;
	return $output;
}

1;
