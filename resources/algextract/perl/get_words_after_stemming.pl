#usr/bin/perl
use strict;
use warnings;
use Lingua::Stem; #Perl modeule for stemming operations

#Function to get unique words from a document 
#Takes as argument a document (represented as an array of words)
#Returns the array of unique words in the docement after stemming.
sub get_words_after_stemming
{
	my $document = shift;
	my $stop_words_ref = shift;
	my %stop_words = %{$stop_words_ref};
	#Split the document into words, convert all to lowercase and remove punctuations except - as it may be used to join 2 words.
	my @words = map { $_ =~ /([a-z0-9|-]+)/} map {lc($_)} split /\s+/s, $document;
	#Remove Stop Words
	#Uses the list of stop words read in main script
	@words = grep {!(exists ($stop_words{$_}))} @words;
    #Perform stemming
	my $stem_word_ref = Lingua::Stem::stem(@words);
	return @{$stem_word_ref};
}	
1;
