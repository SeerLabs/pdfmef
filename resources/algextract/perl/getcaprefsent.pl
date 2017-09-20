#usr/bin/perl
#use warnings;
use strict;
use Cwd;

#This script performs following tasks:
#1. Extracts Figure/Table Captions and the correspoonding page numbers.
#2. Preprocess the text files to remove some of the junk sentences
#3. Carries out sentence segmentation to prepare sentence files for each document.
#4. Extracts Reference Sentences for each caption

#Path where the captions are stored
#my $cap_dir_base = "/opt/sumit/Captions/";
my $cap_dir_base = $ARGV[0]."/Captions/";

#Path where the reference sentences are stored
#my $refsent_dir_base = "/opt/sumit/ReferenceSentences/";
my $refsent_dir_base = $ARGV[0]."/ReferenceSentences/";

#Path where the Sentence Files are stored
#my $sent_dir_base = "/opt/sumit/SentenceFiles/";
my $sent_dir_base = $ARGV[0]."/TextFiles/";

#Read the list of subdirs
#open(my $read,"done2.txt") or die "Can not open read.txt. buhoohooo $!";
#my @dirs = <$read>;
#chomp(@dirs);

#foreach my$subdir (@dirs)
#{

#Make the subdirectories
#my $cap_dir = $cap_dir_base.$subdir;
my $cap_dir = $cap_dir_base;
#my $refsent_dir = $refsent_dir_base.$subdir;
my $refsent_dir = $refsent_dir_base;
#my $sent_dir = $sent_dir_base.$subdir;
my $sent_dir = $sent_dir_base;
#`mkdir $cap_dir $refsent_dir $sent_dir`;


#Read all the test documents in the directory
#my $working_dir_name = "/opt/sumit/TEXTFiles/$subdir";
my $working_dir_name = $ARGV[0]."/text_files/";
opendir (my $working_dir, $working_dir_name) 
            or die "Sorry, Directory can't be opened, $!";
my @files_in_pwd = readdir $working_dir;
#Neglect system files, first two are such files
#Suppawong --> not always true
#my @files_names = @files_in_pwd[2..$#files_in_pwd];
my @files_names = @files_in_pwd[0..$#files_in_pwd];

#Now we will process each text file
foreach my $currentfile (@files_names)
{	
	#skip filename that begins with .
	
	my $temp_currentfile = substr($currentfile, 0, 1); 
	next if($temp_currentfile eq ".");
	print("Processing file $currentfile\n");

	#Read all the file content line by line
	open (my $input_file, $working_dir_name."/".$currentfile) 
	                        or die "Can't open the file : $!" ;
	my @lines = <$input_file>;
	
	
	###############################################################
	#                                                             #
	#                           STEP 0                            #
	#                      Remove References                      #
	#                                                             #
	###############################################################
	my $refLine = 0;
    my $no_of_lines = $#lines;
	my $ii=$no_of_lines;	
	while($ii > 0)
	{   
	    if ($lines[$ii] =~ m/(References|REFERENCES|Reference|REFERENCE)/)
	    {   $refLine = $ii;
	        last;
	     }
	     $ii--;
	 }	   
	 if($refLine/$no_of_lines > 0.8 )
	{@lines = @lines[0..$refLine];}
	
	
	
	
	###############################################################
	#                                                             #
	#                           STEP 1                            #
	#                      EXTRACT CAPTIONS                       #
	#                                                             #
	###############################################################
	
	#Using Regular Expressions to extract caption sentences
	my @captions;#Array of captions
	my $caption_count = 0; #To count the captions found
	my $page_no = 1;#To keep track of the page on which caption is found
    $no_of_lines = $#lines;
	my $templine;
	for(my $i=0;$i<=$no_of_lines;$i++)
	{	$templine = $lines[$i];
		#eliminate whitespaces from templine
		$templine =~ s/\s//g;

		if( ($lines[$i] =~ m/^(<PAGE>)/) )
		{
			$page_no++; #Start of a new page
			$lines[$i]="";
		}
		elsif($templine = m/(....)/)
		#suppawong: skip the table of content line
		{	#do nothing
		}
		else
		{
			if( 
				#($lines[$i] =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM)(\s*)(\d+)(\.|:|-)(\s*)([A-Z])/)
				# || ($lines[$i] =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM)(\s*)(\d+)(\s*)([A-Z])/)
				# || ($lines[$i] =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|TABLE|Table|table|Algorithm|algorithm|ALGORITHM)(\s*)(\d+)(\n|\r)/)
				# || ($lines[$i] =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM)(\s*)(\d+)(\.|-)(\d+)(\.|:|-)(\s*)([A-Z])/)
				# || ($lines[$i] =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM)(\s*)(\d+)(\.|-)(\d+)(\s*)([A-Z])/) 
				# || ( $lines[$i] =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|TABLE|Table|table|Algorithm|algorithm|ALGORITHM)(\s*)(\d+)(\.|-)(\d+)(\n|\r)/)

			#suppawong's revision:	
			($lines[$i]  =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM|Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)(\s*)(\d+)(\.|:|-)(\s*)(\(|[A-Z])/)
				 || ($lines[$i] =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM|Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)(\s*)(\d+)(\s*)(\(|[A-Z])/)
				 || ($lines[$i] =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|TABLE|Table|table|Algorithm|algorithm|ALGORITHM|Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)(\s*)(\d+)(\n|\r)/)
				 || ($lines[$i] =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM|Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)(\s*)(\d+)(\.|-)(\d+)(\.|:|-)(\s*)(\(|[A-Z])/)
				 || ($lines[$i] =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM|Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)(\s*)(\d+)(\.|-)(\d+)(\s*)(\(|[A-Z])/) 
				 || ( $lines[$i] =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|TABLE|Table|table|Algorithm|algorithm|ALGORITHM|Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)(\s*)(\d+)(\.|-)(\d+)(\n|\r)/)

				#Suppawong: "Algorithm 4.2.\n" or "Algorithm 4.\n" or "Algorithm 3.7:      1. S"
				|| ($lines[$i] =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM|Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)(\s*)(\d+)((\.|-)(\d+))?(((\.)(\n|\r))|(\:))/)
			)
			{
				chomp($lines[$i]);
				#This line is the beginning of caption.
				$captions[$caption_count] = $lines[$i];
				$lines[$i]="";
				my $cap_len = 1;
				
				#In case of a multi line caption, we take up to first 2 lines
				# or up to first line break, whichever is earlier.
				while($cap_len != 0 && $cap_len < 2)
				{
					chomp($lines[$i+$cap_len]);
					if ((length($lines[$i+$cap_len]) == 0)||
					         ($lines[$i+$cap_len] =~ m/^(<PAGE)/))
					{$cap_len = 0;}
					else
					{
						$captions[$caption_count] = $captions[$caption_count]." ".$lines[$i+$cap_len];
						#Remove the caption sentences from the file, 
						#it prevents conflicts with reference sentences
						$lines[$i+$cap_len]=""; 
						$cap_len++;
					}
				}
				#Include the page information
				$captions[$caption_count] = $captions[$caption_count]."\n"."<PAGE>".$page_no."\n";
				$caption_count = $caption_count+1;
			}
		}
	}
	
	
	#Writing Captions in a proper format, remove extreanous spaces
	for(my $i=0; $i < $caption_count; $i++)
	{
		if($captions[$i] =~ m/^(\s+)/)
		{
			$captions[$i] =~ s/^(\s+)//;
		}	
	}

	#Write to file
	my $cap_file_name = "$cap_dir/excap_$currentfile";
	open (my $caption_file, ">$cap_file_name")
	             or die "Can't open the caption  output file $currentfile, $! \n";
	print  $caption_file @captions;
	
	
	###############################################################
	#                                                             #
	#                           STEP 2                            #
	#            Pre-processing Step to filter out                #
	#            sparse lines and section headings                #
	#                                                             #
	###############################################################
	
	my %no_of_words_in_line=();
	my %no_of_spaces_in_line=();
	my $average_length_of_lines = 0;
	my $average_no_of_spaces_in_line = 0;
	
	for(my $i=0;$i<=$no_of_lines;$i++)
	{
        $no_of_words_in_line{$i} = $lines[$i] =~ s/((^|\s)\S)/$1/g;
		$average_length_of_lines += $no_of_words_in_line{$i};
		$no_of_spaces_in_line{$i} = $lines[$i] =~ s/(\s|\t)/$1/gi;
		$average_no_of_spaces_in_line += $no_of_spaces_in_line{$i};
    }
	
	if($no_of_lines)
	{
	    $average_length_of_lines /= $no_of_lines;
	    $average_no_of_spaces_in_line /= $no_of_lines;
	}
	
	my $threshold = 0.8*$average_length_of_lines;
	
	for(my $i=0;$i<=$no_of_lines-1;$i++)
	{
		my $length = length($lines[$i]);
		if($length>0)
		{
		    #Filter lines which are end of some sentence
    		if($lines[$i] !~ m/^(\s*)(.*)(\.$)/)
	    	{
	    		if($no_of_spaces_in_line{$i}/$length>.5)
	    		{$lines[$i]="";}
	    		else
	    		{
	    		    if( ($no_of_words_in_line{$i}<$threshold) && 
	    		                    ($no_of_words_in_line{$i+1}==0))
	    		    {$lines[$i] = "";}		
	    	    }
	        }
	    }
    }		
	
	#Now we will carry out sentence segmentation
	###################################################################
	#This code block extracts each sntence from the text file. 
	
	# $text		The whole text as one variable
	# $abbr1	Abbreviations that do not occur at the end of a sentence
	# $abbr2	Abbreviations that can occur at the end of a sentence
	# @sentence	Data in sentence form stored in an array
		
	my $abbr1="M([rs]|rs|me)|Dr|U\\\.S(\\\.A|)|[aApP]\\\.[mM]|Calif|Fla|D\\\.C|N\\\.Y|Ont|Pa|V[Aa]|[MS][Tt]|Jan|Feb|Mar|Apr|Aug|Sept?|Oct|Nov|Dec|Assoc|	[oO]\\\.[kK]|Co|R\\\.V|Gov|Se[nc]|U\\\.N|\[A-Z\]|i\\\.e|e\\\.g|vs?|Re[pv]|Gen|Univ|Jr|[fF]t|[Ss]gt|[Pp]res|[Pp]rof|[Aa]pprox|[Cc]orp|[Dd]ef";
	
	my $abbr2="D\\\.C";
	
	my $i = 0;
	my $line;
	my $text;
	
	# Main Script
	
	foreach (@lines) 
	{				# Read one line from text
		chomp;
		if ( /^[ \t]*$/ )
		{		# Skip if the line is empty
			next;
		} 
		else 
		{
			$line = $_;		# store each line in $line
			$line =~ s/^[ \t]+//;	# Remove white spaces at the beginning of the line
			$line =~ s/  +/ /g;	# Remove neighboring spaces
			$line =~ s/\t//g;	# Remove tab
			$line =~ s/ +$//;	# Remove spaces at the end of line
			$text .= " ".$line;	# Put together all lines
		}
	}
	
	$text = substr($text,1);	# Remove the space at initial position
	
	$text =~ s/\? /\?\n/g;			# New line at ? space
	$text =~ s/! /!\n/g;			# New line at ! space
	$text =~ s/\.\" /\."\n/g;		# New like at ." space
	$text =~ s/\?\" ([A-Z])/\?\"\n$1/g;	# New line at ?" space capital
	$text =~ s/!\" ([A-Z])/!\"\n$1/g;	# New line at !" space capital
	$text =~ s/(\.\?!)\) /$1\)\n/g;		# New line at .) space
	#Sumit
	$text =~ s/(\)\?!)\. /$1\.\n/g;		# New line at .) space
	$text =~ s/\. ([A-Z])/\.\n$1/g;         # New line at . space capital
	$text =~ s/\. \"/\.\n\"/g;              # New line at . space "
	$text =~ s/\" \"/\"\n\"/g;		# New line between " and "
	$text =~ s/\b($abbr1)\.\n/$1\. /g;	# Delete new line at $abbr1
	$text =~ s/\b($abbr2)\. ([A-Z\"])/$1\n$2/g;	# New line at $abbr2
	
	my @sentence = split ( /\n/, $text);	# Store sentences in the array 
	
	foreach my $out ( @sentence ) {
		if ( $out =~ /\".+\"/ ) {	# Skip if " appears more than once
			$i++;
			next;
		} else {
			$sentence[$i] =~ s/\"//;	# Remove "
			$i++;
		}
	}
	
	#Array @sentence contains all the sentences in the file
#############################################################################################
	
	#Writing sentences in a proper	 format, remove extreanous spaces
	for(my $i=0; $i<$#sentence; $i++)
	{
		if($sentence[$i] =~ m/^(\s+)/)
		{$sentence[$i] =~ s/^(\s+)//;}	
	}
	
	#Write to file
	my $sent_file_name = "$sent_dir/sent_$currentfile";
	open (my $sentence_file, ">$sent_file_name") or die "Can't open the sentences output file, $! \n";
	foreach (@sentence)
	{print $sentence_file $_,"\n";}
	
	#Using Regular Expressions to extract reference sentences
	my @ref_sentence;
	my $ref_sentence_count = 0;
	
	foreach(@sentence)
	{
		if($_ =~ m/(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM)(\s*)(\d+)/
		            || m/(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM)(\s*)(\d+)(\.|-)(\d+)/)
		{
		$ref_sentence[$ref_sentence_count] = $_;
		$ref_sentence_count += 1;
		}
	}
	

	#Write reference sentences in the corresponding otput file
	my $refsent_file_name = "$refsent_dir/exref_$currentfile";
	open (my $ref_sentence_file, ">$refsent_file_name") or die "Can't open the Reference output file, $! \n";
	foreach (@ref_sentence)
	{print $ref_sentence_file $_,"\n";}

}
#} 
# report time taken
print "Time taken was ", (time - $^T), " seconds"; 
