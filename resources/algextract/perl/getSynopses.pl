#!/usr/bin/perl
use strict;
use warnings;
use List::Util qw(max);
use List::Util qw(min);
use POSIX qw(ceil floor);

#The following probabilities are computed by training on Dataset used in:
#Summarizing Figures, Tables and Algorithms in Academic Documents
#To Augment Search Results; Sumit Bhatia and Prasenjit Mitra;
#ACM TOIS (Under Review)

#Dependent probabilities
my @dProb1 = (0.293089430894309, 0.328455284552846, 0.15, 0.661382113821138, 0.844308943089431, 0.598780487804878); 
my @dProb0 = (0.706910569105691 ,0.671544715447154 ,0.85 ,0.338617886178862 ,0.155691056910569 ,0.401219512195122);

#Independent probabilities
my @iProb1 = (0.0550095615028209 ,0.0550761590349066 ,0.00445252071658945 ,0.0230617739679761 ,0.0679675384600748 ,0.448382155666974); 
my @iProb0 = (0.944990438497179 ,0.944923840965093 ,0.995547479283411 ,0.976938226032024 ,0.932032461539925 ,0.551617844333026);

#Get the score to prob hash
my %prob = getProbHash(\@iProb1,\@iProb0,\@dProb1,\@dProb0);


#Now classification starts
#Read the input directory containing all features
#my $featureDir = "./Features";
my $featureDir = $ARGV[0]."/Features/";

opendir (my $inputdir, $featureDir) 
            or die "Sorry, Directory can't be opened, $!";
my @files = readdir $inputdir;
#Neglect system files, first two are such files

#this is not ordered list
my @filesNames = @files[0..$#files];
chomp(@filesNames);

foreach(@filesNames)
{	#suppawong:
	next if(index($_, '.') == 0); #system files


    #Extract text file name
    my @realName = ();
    if($_ =~ m/_Fig_/)
    {@realName = split(/_Fig_/,$_);}
    
    if($_ =~ m/_Table_/)
    {@realName = split(/_Table_/,$_);}
    
    if($_ =~ m/_Algo_/)
    {@realName = split(/_Algo_/,$_);}
    
    print "\nfilename is ".$_."\n";
    
    
    my $textFileName = "sent_$realName[0].txt";
    
    
    #Read features for this docEl
	#my $name = "./Features/".$_;
	my $name = $ARGV[0]."/Features/".$_;
	
    open(my $h,$name);
    my @testFeatures = <$h>;
    chomp(@testFeatures);
 
    my %sentNo = ();#feature point number -> sent no in text file
    my %scores = ();#feature point number -> score
    
    #Compute scores for each test sentence now
    for(my $testpoint=0;$testpoint<(scalar @testFeatures);$testpoint++)
    {
    	#Get the list of features
	    my @features = map { $_ =~ /([a-z0-9|-]+)/} map {lc($_)} split /\s+/s, $testFeatures[$testpoint];
	    chomp(@features);
	    
	    #Find Sent No
	    $sentNo{$testpoint} = $features[6];
	
	    $scores{$testpoint}=0;
	    my $nr=1;
	    my $dr=1;
	    
	    for(my $j=0;$j<6;$j++)
	    {
	        if($features[$j]>0)
	        {
	            $nr*=$dProb1[$j];
	            $dr*=$iProb1[$j];
	        }
	        else
	        {
	            $nr*=$dProb0[$j];
	            $dr*=$iProb0[$j];
	        }
	    }
	    my $temp = $nr/$dr;
	    $scores{$testpoint} = $prob{$temp};
    }
    
    #Scores now contain the scores for all the sentences
  	#Keys are the respective sentence numbers
    #Sort the sentences by Score values
    my @rankedlist = sort {$scores{$b} <=> $scores{$a}} (keys(%scores));
    #Ranked list now contains the sentences numbers in decreasing order of their scores
    
    #Use the utility function to generate the synopses
    #suppawong: try if this increase the number of words in synopses
    my $lambda = 0.15;
    #my $lambda = 0.7;
    my %synopsis=(); #sentence no to score
    my $continue=1;
    my $synopCount=0;
    while($continue)
    {
        $continue=0;
        my $u = $scores{$rankedlist[$synopCount]} - (1 - exp(-1*$lambda*($synopCount)));
        if ($u>0)
        {
            $synopsis{$rankedlist[$synopCount]} = $scores{$rankedlist[$synopCount]};
            $synopCount++;
            $continue=1;
        }
     }
    
    #Get the list of actual sentence numbers
    my @sentNo = ();
    for(my $s=0;$s<$synopCount;$s++)
    {$sentNo[$s] = $sentNo{$rankedlist[$s]};}
    @sentNo = sort {$a <=> $b} @sentNo;
    foreach(@sentNo){print "$_ ";}
    print "\n";
    #Read the text file
    #open(my $text,"./TextFiles/".$textFileName) or die "Cant open Text File,$!";
    print $ARGV[0]."/TextFiles/".$textFileName;
    open(my $text,$ARGV[0]."/TextFiles/".$textFileName) or die "Cant open Text File,$!";
    my @sentences = <$text>;
    #Open output file
    #open(my $syn,">./Synopses/$_") or die "Cant open Synopses File,$!";
    open(my $syn,">".$ARGV[0]."/Synopses/".$_) or die "Cant open Synopses File,$!";
        
    #Make the synopses string
		my $synopsis;
		chomp($sentences[$sentNo[0]]);
		$synopsis = $sentences[$sentNo[0]];
		
		for (my$k=1;$k<$synopCount;$k++)
		{ chomp($sentences[$sentNo[$k]]);
			if($sentNo[$k] == $sentNo[$k-1]+1)
			{$synopsis = $synopsis." ".$sentences[$sentNo[$k]];}
		    else
		    {$synopsis = $synopsis." ... ".$sentences[$sentNo[$k]];}
		}
    print $syn "$synopsis\n\n";
    
}

################################################################################

sub dec2bin
{
    my $no = shift;
    my @dec = shift;
    my $count=0;
    while($no>0)
    {
        my $rem = $no%2;
        $dec[$count] = $rem;
        $no = floor($no/2);
        $count++;
     }   
     while($count<6)
     {$dec[$count]=0;$count++;} 
     return @dec;    
}

sub getProbHash
{
    my $iProb1Ref = shift;
    my $iProb0Ref = shift;
    my $dProb1Ref = shift;
    my $dProb0Ref = shift;

    my @iProb1 = @{$iProb1Ref};
    my @iProb0 = @{$iProb0Ref};
    my @dProb1 = @{$dProb1Ref};
    my @dProb0 = @{$dProb0Ref};
    
    my %prob = ();
    
    for(my $i=0;$i<64;$i++)
    {
        my @features = ();
        @features = dec2bin($i,@features);
        #@features now contain feature selection
        my $nr=1;
        my $dr=1;
        
        for(my $j=0;$j<6; $j++)
        {
            if($features[$j] == 1)
            {
                $nr *= $dProb1[$j];
                $dr *= $iProb1[$j];
            }
            else
            {
                $nr *= $dProb0[$j];
                $dr *= $iProb0[$j];
            }
        }
        $prob{$nr/$dr} = $i;
     }
     
     #Now we have all the possible probability values
     #Let us rank them
     my @rankedlist = sort {$b <=> $a} (keys(%prob));
     for(my $k=0;$k<64;$k++)
     {
        my $prob = (64-$k)/64;
        if(!(exists($prob{$rankedlist[$k]})))
        {print "ERROR\n";}
        $prob{$rankedlist[$k]}=$prob;
     }
        
     
    return %prob;

}   
