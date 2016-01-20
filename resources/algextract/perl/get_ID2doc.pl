#usr/bin/perl
use strict;
use warnings;

sub get_id2doc
{
	my $documents = shift;
	my @documents = @{$documents};
	#create a lookup hash for document to document ID conversion
	my %doc_id = ();
	my $id = 0;
	#Asign a unique ID to each document
	foreach (@documents)
	{if(!(exists $doc_id{$_}))
	{$doc_id{$_} = $id++;}}
	return \%doc_id;
}
1;