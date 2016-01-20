#/usr/bin/perl
use strict;
use warnings;
use List::Util qw(max);
use Lingua::Stem qw(stem);

#suppawong: for sample collecting
use List::Util qw/shuffle/; 

#usr/bin/perl
use strict;
use warnings;
use Lingua::Stem; #Perl modeule for stemming operations


require $ARGV[2]."/get_ID2doc.pl";
#require $ARGV[2]."/idx.pl"; #To create inverted index
require $ARGV[2]."/get_words_after_stemming.pl";
require $ARGV[2]."/get_words.pl";

#Takes reference to an array of documents and returns an inverted index
#Inverted index represented by a hash table (term -> list of document ids)
sub get_idx
{
	
	my $id2doc_ref = shift;
	my $stop_word_ref = shift;
	my %id2doc = %{$id2doc_ref};
	
	#Start creating the INVERTED INDEX
	my %idx = (); #term -> posting list
	foreach my $id (keys %id2doc)
	{
		my @doc = $id2doc{$id};
		@doc = get_words(@doc,$stop_word_ref);
		foreach(@doc)
		{push @{$idx{$_}}, $id;}
	}
	#Yippie!!! Inverted index created
	
	return \%idx;	
}

# This script reads all the TEXT files in the given directory
# and computes different features 
# for the sentences in the text file and writes them in a file.

#Path where the captions are stored
#my $cap_dir = "./Captions";
my $cap_dir = $ARGV[0]."/Captions/";
#Path where the reference sentences are stored
#my $refsent_dir = "./ReferenceSentences";
my $refsent_dir = $ARGV[0]."/ReferenceSentences/";
#Path where the text files are stored (after sentence segmentation
#my $inputdirName = "./TextFiles";
my $inputdirName = $ARGV[0]."/TextFiles/";
#my $outputdirName = "./Features";
my $outputdirName = $ARGV[0]."/Features/";

#suppawong: for sample collection
my $random_mode = $ARGV[1]; #y or n
my $numfiles = 0;
my $MAXNUMFILES = 100;

#Read the input directory
opendir (my $inputdir, $inputdirName) 
            or die "Sorry, Directory can't be opened, $!";
my @files = readdir $inputdir;
#Neglect system files, first two are such files
#Suppawong: Not always true. Would be better to filter out files whose filenames begin with '.'
#my @files_names = @files[2..$#files];
my @files_names = @files[0..$#files];

#Read the list of stop words
my %stopwords=();
#Read list of stopwords
open(my $STOPLIST, $ARGV[2]."/stopwords.txt")
    or die "Sorry, file can't be opened, $!";
	my @stop = <$STOPLIST>;
	foreach(@stop)
	{
		chomp;
		$stopwords{$_}++;
	}
	
#Make CuePhrase Hash
open(my $cue,$ARGV[2]."/cue.txt")
            or die "Cue phrase file can not be opened, $!";
my @cuephrases = <$cue>;
chomp(@cuephrases);
@cuephrases = @{stem(@cuephrases)};
foreach(@cuephrases)
{print $_,"\n";}
my %cue = ();
foreach(@cuephrases)
{$cue{$_}++;}
     
my $noOfDocels =0;
my $noOfRef=0;
my $length=0;        
################################################################################    
#suppawong: select sample files
if($random_mode eq 'y')
{
	
	#my @randfiles = (shuffle(@files_names))[0..$MAXNUMFILES-1];
	#@files_names = @randfiles;
	@files_names = shuffle(@files_names);
	#print scalar @files_names;
}

#################################################################################    

#suppawong
open (algocountFile, '>algo_count.txt');
#Suppawong: get caption-ref sentence mapping
open(my $mapout, ">".$ARGV[0]."/CaptionMaps/map.txt") or die "Can not open output file, $!";

foreach my $fileName(@files_names)
{	#suppawong
	if($random_mode eq 'y' && $numfiles > $MAXNUMFILES)
	{	
		last;
	}
	
	my $temp_filename = substr($fileName, 0, 1); 
	next if($temp_filename eq ".");
	
	print "Processing $fileName\n";
	
    open(my $file,$inputdirName."/".$fileName)
        or die "Sorry, FILE can not be opened :-(, $!";
    my @docs = <$file>;
    chomp(@docs);
    #suppawong: why substr filename
	$fileName = substr($fileName,5);
	print algocountFile $fileName.",";

    #Read caption file
	#my $caption = "./Captions/excap_".$fileName;
	my $caption = $cap_dir."/excap_".$fileName;
	open(my$cap,$caption) or die "Sorry, file $caption can't be opened, $!";
	my @cap = <$cap>;
	#print @cap,"\n";
	
	#Read reference sentences
	#my $refsent = "./ReferenceSentences/exref_".$fileName;
	my $refsent = $refsent_dir."/exref_".$fileName;
	open(my $ref,$refsent)
	    or die "Sorry, file can't be opened, $!";
	my @refsent = <$ref>;
	#print @refsent,"\n";
	
	
	#Create hash table for converting from doc ids to doc and vice versa
	my %doc2id = %{get_id2doc(\@docs)};
	#create a lookup hash for document ID to document conversion
	my %id2doc = reverse %doc2id;
	
	#Create inverted index for the paper.
	my %idx = %{get_idx(\%id2doc,\%stopwords)};
	
	#Compute IDFs for each term
	my %idf; # term -> IDF
	foreach(keys %idx)
	{
		$idf{$_} = scalar @{$idx{$_}};#This is DF
		$idf{$_} = log((scalar keys %id2doc)/($idf{$_}))/log(10);#This is IDF
	}
    
    #Create the term document matrix for the paper
	#Term document matrix; 
	#document id -> reference to array of words (after stemming) in documents
	my %tdmat;
	#my @list_of_words;
	my %Ld; #Document length; id->length
	foreach (keys %id2doc)
	{	
		my @doc = $id2doc{$_};
		@doc = get_words_after_stemming(@doc,\%stopwords);
		$tdmat{$_} = \@doc;
		#compute length of each document
		$Ld{$_} = scalar @doc;
	}
    
    #Document-Element Type Hash
	my %docelType = (
	    'FIGURE' => 'Fig',
        'FIG.' => 'Fig',
        'Figure' => 'Fig',
        'Fig.' => 'Fig',
        'figure' => 'Fig',
        'fig.' => 'Fig',
        'Table' => 'Table',
        'TABLE' => 'Table',
        'table' => 'Table',
        'Algorithm' => 'Algo',
        'ALGORITHM' => 'Algo',
        'Algo' => 'Algo',
        'ALGO' => 'Algo',
        'algortihm' => 'Algo',
        'algo' => 'Algo',
			'Pseudocode' => 'Algo',
			'pseudocode' => 'Algo',
			'PSEUDOCODE' => 'Algo',
			'Pseudo-code' => 'Algo',
			'pseudo-code' => 'Algo',
			'PSEUDO-CODE' => 'Algo',
			'Pseudo code' => 'Algo',
			'pseudo code' => 'Algo',
			'PSEUDO CODE' => 'Algo'
        );
    #Now, we start computing features docel by docel

#suppawong:
my $numcapsinfile = 0;
my $numcapswithsyn = 0;

CAPLOOP:	
for(my $i=0; $i<=$#cap; $i++)
	{
		
		
		
		
		my $caption = $cap[$i];
		chomp($caption);
		#Extract Page Number
		(my $tag, my $pageno) = ($cap[$i+1]=~ m/(<PAGE>)(\d+)/);
		
		#suppawong: need to filter out those caption without 'algorithm' here, not there
		my $temp_caption = $caption;
		$temp_caption =~ s/\s//g; 
		
		#pseudocode of algorithm
		if ($caption =~ m/^(\s*)(.*)(Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)(\s)(of|for)(\s)(.*)(Algorithm|algorithm|ALGORITHM)(.*)/)
		{	#do nothing
		}
		# preposition+algorithm (such as "result of the algorithm")
		elsif($caption =~ m/^(\s*)(.*)(\s)(of|by|for|with|in)(\s)(.*)(Algorithm|algorithm|ALGORITHM|Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)(.*)/)
		{	next CAPLOOP
		}


		#Suppawong: check if this is a page content line
		if($temp_caption = m/(....)/)
		{	print "@@@@ Table of Content Line: ".$caption."\n";
			next CAPLOOP
		}
		elsif ($caption =~ m/(Algorithm|ALGORITHM|Algo|ALGO|algorithm|algo|Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)/)
		{	$numcapsinfile = $numcapsinfile + 1;
		}
		else
		{next CAPLOOP}

		#my @combined_query = $query;
		#Extract the docel number
		
		#(my $docel, my $space, my $cap_no) =
		    #($caption =~ m/(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|ALGORITHM|Algo|ALGO|algorithm|algo)(\s*)(\d+)/);
		    
		#suppawong: need to add more rules
		my $docel = '';
		my $cap_no = '';
		if($caption  =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM|Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)(\s*)(\d+)(\.|:|-)(\s*)(\(|[A-Z])/)
		{	(my $space1,  $docel, my $space2,  $cap_no) = ($caption  =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM|Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)(\s*)(\d+)(\.|:|-)(\s*)(\(|[A-Z])/);
		}
		elsif($caption =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM|Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)(\s*)(\d+)(\s*)(\(|[A-Z])/)
		{	(my $space1, $docel, my $space2,  $cap_no) = ($caption =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM|Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)(\s*)(\d+)(\s*)(\(|[A-Z])/);
		}
		elsif($caption =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|TABLE|Table|table|Algorithm|algorithm|ALGORITHM|Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)(\s*)(\d+)(\n|\r)/)
		{	(my $space1, $docel, my $space2, $cap_no) = ($caption =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|TABLE|Table|table|Algorithm|algorithm|ALGORITHM|Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)(\s*)(\d+)(\n|\r)/);
		}
		elsif($caption =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM|Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)(\s*)(\d+)(\.|-)(\d+)(\.|:|-)(\s*)(\(|[A-Z])/)
		{	(my $space1, $docel, my $space2, my $cap_no1, my $delim, my $cap_no2) = ($caption =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM|Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)(\s*)(\d+)(\.|-)(\d+)(\.|:|-)(\s*)(\(|[A-Z])/);
			$cap_no = $cap_no1.$delim.$cap_no2;
		}
		elsif($caption =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM|Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)(\s*)(\d+)(\.|-)(\d+)(\s*)(\(|[A-Z])/)
		{	(my $space1, $docel, my $space2, my $cap_no1, my $delim, my $cap_no2) = ($caption =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM|Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)(\s*)(\d+)(\.|-)(\d+)(\s*)(\(|[A-Z])/);
			$cap_no = $cap_no1.$delim.$cap_no2;
			
		}
		elsif($caption =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|TABLE|Table|table|Algorithm|algorithm|ALGORITHM|Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)(\s*)(\d+)(\.|-)(\d+)(\n|\r)/)
		{	(my $space1, $docel, my $space2, my $cap_no1, my $delim, my $cap_no2) = ($caption =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|TABLE|Table|table|Algorithm|algorithm|ALGORITHM|Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)(\s*)(\d+)(\.|-)(\d+)(\n|\r)/);
			$cap_no = $cap_no1.$delim.$cap_no2;
		}
		elsif($caption =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM|Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)(\s*)(\d+)(((\.)(\n|\r))|(\:))/)
		{	(my $space1, $docel, my $space2, my $cap_no1) = ($caption =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM|Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)(\s*)(\d+)(((\.)(\n|\r))|(\:))/);
			$cap_no = $cap_no1;
		}
		elsif($caption =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM|Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)(\s*)(\d+)(\.|-)(\d+)(((\.)(\n|\r))|(\:))/)
		{	(my $space1, $docel, my $space2, my $cap_no1,  my $delim, my $cap_no2) = ($caption =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM|Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)(\s*)(\d+)(\.|-)(\d+)(((\.)(\n|\r))|(\:))/);
			$cap_no = $cap_no1.$delim.$cap_no2;
		}
		else
		{	print "@@@@ Error Caption: ".$caption."\n";
		}
		
		print "@@@@ doc: ".$fileName."|".$docel."|".$cap_no."\n";
		    
		    #only need algorithm
		    #($caption =~ m/(Algorithm|ALGORITHM|Algo|ALGO|algorithm|algo)(\s*)(\d+)/);
		
		#Suppawong: get caption-ref sentence mapping
		my $fileID = substr($fileName,0,-4);
		my $featureFileID = substr($fileName,0,-4)."_$docelType{$docel}_$cap_no";			
		print $mapout "<:algorithm:>\n<:info:>$fileID<###>$pageno<###>$featureFileID<###>$caption\n";
		
		#Find all reference sentences
		my @ref; #array to store all references to a figure
		my $no_of_ref = 0;#To store how many times a figure has been referenced.
		foreach(@refsent)
		{	
			#(my $docel1, my $space1, my $ref_no) = 
			    #($_=~ m/(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|ALGORITHM|Algo|ALGO|algorithm|algo)(\s*)(\d+)/);
			
			#Suppawong: need to add more rules
			my $docel1;
			my $ref_no;
			if($_=~ m/(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|ALGORITHM|Algo|ALGO|algorithm|algo|Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)(\s*)($cap_no)/)
			{
				($docel1, my $space1, $ref_no) = 
			    ($_=~ m/(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|ALGORITHM|Algo|ALGO|algorithm|algo|Pseudocode|pseudocode|PSEUDOCODE|Pseudo-code|pseudo-code|PSEUDO-CODE|Pseudo code|pseudo code|PSEUDO CODE)(\s*)($cap_no)/);
			 }
			 else
			 {	#print "@@@@ Error Refsent: ".$_."\n";
				#print "##### Can't find ".$docel."|".$cap_no."\n";
			 }
			   
			    
# 			my $docel1;
# 			my $ref_no;
# 			if($_  =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM)(\s*)(\d+)(\.|:|-)(\s*)([A-Za-z])/)
# 			{	(my $space1, $docel1, my $space2, $ref_no) = ($_  =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM)(\s*)(\d+)(\.|:|-)(\s*)([A-Z])/);
# 			}
# 			elsif($_ =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM)(\s*)(\d+)(\s*)([A-Za-z])/)
# 			{	(my $space1, $docel1, my $space2, $ref_no) = ($_ =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM)(\s*)(\d+)(\s*)([A-Z])/);
# 			}
# 			elsif($_ =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|TABLE|Table|table|Algorithm|algorithm|ALGORITHM)(\s*)(\d+)(\n|\r)/)
# 			{	(my $space1, $docel1, my $space2, $ref_no) = ($_ =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|TABLE|Table|table|Algorithm|algorithm|ALGORITHM)(\s*)(\d+)(\n|\r)/);
# 			}
# 			elsif($_ =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM)(\s*)(\d+)(\.|-)(\d+)(\.|:|-)(\s*)([A-Za-z])/)
# 			{	(my $space1, $docel1, my $space2, my $ref_no1, my $delim, my $ref_no2) = ($_ =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM)(\s*)(\d+)(\.|-)(\d+)(\.|:|-)(\s*)([A-Z])/);
# 				$ref_no = $ref_no1.$delim.$ref_no2;
# 			}
# 			elsif($_ =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM)(\s*)(\d+)(\.|-)(\d+)(\s*)([A-Za-z])/)
# 			{	(my $space1, $docel1, my $space2, my $ref_no1, my $delim, my $ref_no2) = ($_ =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|Table|table|TABLE|Algorithm|algorithm|ALGORITHM)(\s*)(\d+)(\.|-)(\d+)(\s*)([A-Z])/);
# 				$ref_no = $ref_no1.$delim.$ref_no2;
# 				
# 			}
# 			elsif($_ =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|TABLE|Table|table|Algorithm|algorithm|ALGORITHM)(\s*)(\d+)(\.|-)(\d+)(\n|\r)/)
# 			{	(my $space1, $docel1, my $space2, my $ref_no1, my $delim, my $ref_no2) = ($_ =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|TABLE|Table|table|Algorithm|algorithm|ALGORITHM)(\s*)(\d+)(\.|-)(\d+)(\n|\r)/);
# 				$ref_no = $ref_no1.$delim.$ref_no2;
# 			}
# 			elsif($_ =~ m/^(\s*)(FIGURE|FIG.|Figure|Fig.|figure|fig.|TABLE|Table|table|Algorithm|algorithm|ALGORITHM)(\s*)(\d+)(((\.|-)(\d+))*)(\)*)(\n|\r)/)
# 			{	(my $space1, my $space2,  $docel1, my $space2, my $ref_no1, my $delim, my $ref_no2) = ($_ =~ m/^(\s*)(\(?|\[?)(FIGURE|FIG.|Figure|Fig.|figure|fig.|TABLE|Table|table|Algorithm|algorithm|ALGORITHM)(\s*)(\d+)(((\.|-)(\d+))*)(\)?|\]?)(\n|\r)/);
# 				$ref_no = $ref_no1.$delim.$ref_no2;
# 			}
# 			else
# 			{	print "@@@@ Error Refsent: ".$_."\n";
# 			}

			   
			 #only need algorithm
			#($_=~ m/(Algorithm|ALGORITHM|Algo|ALGO|algorithm|algo)(\s*)(\d+)/);
            
			#A reference is found
			if(exists ($docelType{$docel1}))
			{
    			if( ($docelType{$docel1} eq $docelType{$docel}) && ($ref_no == $cap_no) )
	    		{	print $mapout "$_\n";
	    			$ref[$no_of_ref]=$_;
	    			#$combined_query[0] = $combined_query[0]." ".$ref[$no_of_ref];
	    			#chomp($combined_query[0]);
	    			$no_of_ref++;
	    		}
	    	}
	    }
	    #Suppawong: get caption-reference sentence mapping
	    print $mapout "<:/algorithm:>\n\n";
	    
		chomp(@ref);
		
    if((scalar @ref) > 0)
    {
        $noOfDocels++;
        $noOfRef+=$#ref+1;
        #Compute features only if both cap and refsent are there
        #Compute Caption Similarity feature for this docel
        #Get unique words in the caption
        my @caption = get_words($caption,\%stopwords);
        my %capSimFeature = (); # id -> tf-idf score with caption
        %capSimFeature = %{getSimFeature(\%tdmat,\@caption,\%idf)};
        #Normalize the score in [0-1]
        %capSimFeature = %{normalize(\%capSimFeature)};
        #Discretize the scores, only top 20 are retained
        %capSimFeature = %{discretize(\%capSimFeature)};
        #print "Caption is @caption \nSimilarity\n";
        #foreach(keys %capSimFeature)
        #{print "Score for document $_ is $capSimFeature{$_}\n";}
        
        
        #Compute ReferenceSentence Similarity feature for this docel
        my %refSimFeature = (); # id -> tf-idf score with refsent
        my @refsent = get_words($ref[0],\%stopwords);
        %refSimFeature = %{getSimFeature(\%tdmat,\@refsent,\%idf)};
        
        if((scalar @ref) > 1)
        {
            for(my $refsentNo=1;$refsentNo<=$#ref;$refsentNo++)
            {
                my @anotherRefsent = get_words($ref[$refsentNo],\%stopwords);
                my %temp = %{getSimFeature(\%tdmat,\@anotherRefsent,\%idf)};
                foreach (keys %temp)
                {$refSimFeature{$_} += $temp{$_};}
            }
        } 
        #Normalize the score in [0-1]
        %refSimFeature = %{normalize(\%refSimFeature)};
        #Discretize the scores, only top 10 are retained
        %refSimFeature = %{discretize(\%refSimFeature)};

        #print "Reference Similaruty\n";
        #foreach(keys %refSimFeature)
        #{print "Score for document $_ is $refSimFeature{$_}\n";}   
        
        #Compute IfRefSent feature
        my %ifRefSent = (); #id -> bool (if refsent or not)
        foreach (keys %tdmat)
        {$ifRefSent{$_}=0;}
        foreach (@ref)
        {$ifRefSent{$doc2id{$_}}=1;}
        #print "IfReferenceSentence Fetaures\n";
        #foreach(keys %ifRefSent)
        #{print "Is document $_ is a reference sentence : $ifRefSent{$_}\n";}   
    
        #isInSamePara feature
        #Write now there is no simple way to do this, so do it manually
        my %isInSamePara = (); #id -> bool (if same para or not)
        foreach (keys %tdmat)
        {$isInSamePara{$_}=0;}
        
		#The following commented block was used when we had manual labels for
		#paragraphs
        #my $parastart;
        #my $paraend;
        #for(my $i=0;$i<=$#para;$i++)
        #{
        #    if ($para[$i] =~ m/(<)($docelType{$docel})(\s)($cap_no)/)
        #    {$parastart = $i+1;last;}
        #}
        #for(my $i=$parastart;$i<=$#para;$i++)
        #{
        #    if ($para[$i] =~ m/(<\/)($docelType{$docel})(\s)($cap_no)/)
        #    {$paraend = $i-1;last;}
        #}
                
        #for(my $i=$parastart;$i<=$paraend;$i++)
        #{$isInSamePara{$para[$i]-1}= 1;}
		
		#We mark sentences in postions +-3 from reference sentences as belonging
		#to the same paragraph.
		foreach (@ref)
        {
			my $refSentPos = $doc2id{$_};
			for(my $k=1;$k<=3;$k++)
			{
				$isInSamePara{$refSentPos-$k}=1;
				$isInSamePara{$refSentPos+$k}=1;
			}
		}
        
        #Compute Proximity Feature
        my %proximity = ();
        foreach (keys %tdmat)
        {$proximity{$_}=0;}
        foreach (@ref)
        {
            my $center = $doc2id{$_};
            $proximity{$center} += 1;
            for (my $i= 1; $i <11;$i++)
            {
                if(($center-$i)>=0)
                {$proximity{$center-$i} = 1};#+= exp (-.5* $i);}
                if(($center+$i)<=$#docs)
                {$proximity{$center+$i} = 1};#+=exp (-.5 * $i);}
            }
            
            for (my $i= 6; $i < 11;$i++)
            {
               if(($center-$i)>=0)
             {$proximity{$center-$i} = 1;} #+= exp (-.5 * $i);}
             if(($center+$i)<=$#docs)
            {$proximity{$center+$i} = 1;}#+=exp (-.5 * $i);}
            }
         }
         #Normalize the score in [0-1]
         #%proximity = %{normalize(\%proximity)};
         
        #Compute Cue-Phrase feature
        my%cuePhraseFeature = ();
        foreach (keys %tdmat)
        {$cuePhraseFeature{$_}=0;}
        
        foreach my $sent (keys %cuePhraseFeature)
        {
         my @temp =  grep {(exists ($cue{$_}))} @{$tdmat{$sent}};
         if ((scalar @temp)>0)  
         {$cuePhraseFeature{$sent}=1;}
        }
        
        #Find out class of each sentence
        #my $start;
        #my $end;
        #for(my $i=0;$i<=$#synopsis;$i++)
        #{
        #    if ($synopsis[$i] =~ m/(<)($docelType{$docel})(\s)($cap_no)/)
        #    {$start = $i+1;last;}
        #}
        #for(my $i=$start;$i<=$#synopsis;$i++)
        #{
        #    if ($synopsis[$i] =~ m/(<\/)($docelType{$docel})(\s)($cap_no)/)
        #    {$end = $i-1;last;}
        #}
        #$length+=($end-$start+1);
        #print "$start $end\n";
        #my%label = ();
        #foreach (keys %tdmat)
        #{$label{$_}=-1;}
        #for(my $i=$start;$i<=$end;$i++)
        #{$label{$synopsis[$i]-1}= 1;}
        
        #Now we have all the features, save them in a file
        #my $featureFileName = ">./Features/".substr($fileName,0,-4)."_$docelType{$docel}_$cap_no\.txt";
        my $featureFileName = ">".$outputdirName."/".substr($fileName,0,-4)."_$docelType{$docel}_$cap_no\.txt";
       open(my$out,$featureFileName) or die "Can not open output file, $!";

		#suppawong
		$numcapswithsyn = $numcapswithsyn + 1;
       #Note keys of tdmat are sentence numbers, so we should record them also
       foreach(keys %tdmat)
       {
            #For SVM
            #print $out "$label{$_} 1:$capSimFeature{$_} 2:$refSimFeature{$_} ";
            #print $out "3:$ifRefSent{$_} 4:$isInSamePara{$_} 5:$proximity{$_} 6:$cuePhraseFeature{$_}\n";
            
            #For Naive-Bayes
            print $out "$capSimFeature{$_} $refSimFeature{$_} $ifRefSent{$_} $isInSamePara{$_} $proximity{$_} $cuePhraseFeature{$_} $_\n";

       }   
       $numfiles = $numfiles + 1;    
       
       
}#End if            

}#End for each caption
    print algocountFile "$numcapsinfile,$numcapswithsyn\n";

}#End for each file

#suppawong
close(algocountFile);
#suppawong
close($mapout);

print "\n In $noOfDocels, $noOfRef reference sentences were there, with total synop length = $length\n";
################################################################################

sub getSimFeature
{
    my $tdmatRef = shift;
    my $queryRef = shift;
    my $idfRef  = shift;
    my %tdmat = %$tdmatRef;
    my @query = @$queryRef;
    
    my %sim = ();
    foreach (keys %tdmat)
    {$sim{$_}=getSim(\@query,$tdmat{$_},$idfRef);}
    
    return \%sim;
}

sub getSim
{
    my $queryRef = shift;
    my $sentenceRef = shift;
    my $idfRef = shift;
    my @query = @$queryRef;
    my @sentence = @$sentenceRef;
    my %idf = %$idfRef;
    
    my $score = 0;
    foreach my $qterm (@query)
    {
        my $termweight = 0;
        if(exists ($idf{$qterm}))
        {
            foreach my $sterm (@sentence)
            {if ($sterm =~ m/$qterm/i){$termweight++;}}
            $termweight *= $idf{$qterm};
        }
        $score+=$termweight;
    }
    return $score;
    
}	

sub normalize
{
    my $hashref = shift;
    my%score = %{$hashref};
    
    my @score_val = values %score;
	my $max = max @score_val;
	
	#suppawong: bug Divided by Zero
	if($max != 0)
	{
		foreach (keys %score)
		{$score{$_}/=$max;}
	}
	return \%score;

}


sub discretize
{
    my $hashref = shift;
    my %score = %{$hashref};
 
    my @rankedlist = sort {$score{$b} <=> $score{$a}} (keys(%score));
    
    foreach(keys %score)
    {$score{$_}=0;}
    foreach(@rankedlist[0..19])
    {if($_ > 0){$score{$_}=1};}
    
    return \%score;
}



