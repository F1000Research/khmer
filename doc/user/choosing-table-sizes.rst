.. vim: set filetype=rst

==========================
Setting khmer memory usage
==========================

If you look at the documentation for the scripts (:doc:`scripts`) you'll
see a :option:`-M` parameter that sets the maximum memory usage for
any script that uses k-mer counting tables or k-mer graphs.  What is this?

khmer uses a special data structure that lets it store counting tables
and k-mer graphs in very low memory; the trick is that you must fix
the amount of memory khmer can use before running it. (See `Pell et
al., 2012 <http://www.ncbi.nlm.nih.gov/pubmed/22847406>`__ and `Zhang
et al., 2014 <http://www.ncbi.nlm.nih.gov/pubmed/25062443>`__ for the
details.)  This is what the :option:`-M` parameter does.

If you set it too low, khmer will warn you to set it higher at the end.
See below for some good choices for various kinds of data.

**Note for khmer 1.x users:** as of khmer 2.0, the :option:`-M`
parameter sets the :option:`-N`/:option:`--n_tables` and
:option:`-x`/:option:`--max_tablesize` parameters automatically.
You can still set these parameters directly if you wish.

The really short version
========================

There is no way (except for experience, rules of thumb, and intuition) to
know what this parameter should be up front.  So, use the maximum
available memory::

  -M 16e9

for a machine with 16 GB of free memory, for example.

The short version
=================

This parameter specifies the maximum memory usage of the primary data
structure in khmer, which is basically N big hash tables of size x.
The **product** of the number of hash tables and the size of the hash
tables specifies the total amount of memory used, which is what the
:option:`-M` parameter sets.

These tables are used to track k-mers.  If they are too small, khmer
will fail in various ways (and will complain), but there is no harm
in making it too large. So, **the absolute safest thing to do is to
specify as much memory as is available**.  Most scripts will inform
you of the total memory usage, and (at the end) will complain if it's
too small.

Life is a bit more complicated than this, however, because some scripts --
load-into-counting and load-graph -- keep ancillary information that will
consume memory beyond this table data structure.  So if you run out of
memory, decrease the table size.

Also see the rules of thumb, below.

The real full version
=====================

khmer's scripts, at their heart, represents k-mers in a very memory
efficient way by taking advantage of two data structures, `Bloom
filters <http://en.wikipedia.org/wiki/Bloom_filter>`__ and `Count-Min
Sketches <http://en.wikipedia.org/wiki/Count%E2%80%93min_sketch>`__, that are
both *probabilistic* and *constant memory*.  The "probabilistic" part
means that there are false positives: the less memory you use, the
more likely it is that khmer will think that k-mers are present when
they are not, in fact, present.

Digital normalization (normalize-by-median and filter-abund) uses
the Count-Min Sketch data structure.

Graph partitioning (load-graph etc.) uses the Bloom filter data structure.

The practical ramifications of this are pretty cool.  For example,
your digital normalization is guaranteed not to increase in memory
utilization, and graph partitioning is estimated to be 10-20x more
memory efficient than any other de Bruijn graph representation.  And
hash tables (which is what Bloom filters and Count-Min Sketches use)
are really fast and efficient.  Moreover, the optimal memory size for
these primary data structures is dependent on the number of k-mers,
but not explicitly on the size of k itself, which is very unusual.

In exchange for this memory efficiency, however, you gain a certain
type of parameter complexity.  Unlike your more typical k-mer package
(like the Velvet assembler, or Jellyfish or Meryl or Tallymer), you
are either guaranteed not to run out of memory (for digital
normalization) or much less likely to do so (for partitioning).

The biggest problem with khmer is that there is a minimum hash number
and size that you need to specify for a given number of k-mers, and
you cannot confidently predict what it is before actually loading in
the data.  This, by the way, is also true for de Bruijn graph
assemblers and all the other k-mer-based software -- the final memory
usage depends on the total number of k-mers, which in turn depends on
the true size of your underlying genomic variation (e.g. genome or
transcriptome size), the number of errors, and the k-mer size you
choose (the k parameter) `[ see Conway & Bromage, 2011 ]
<http://www.ncbi.nlm.nih.gov/pubmed?term=21245053>`__.  **The number
of reads or the size of your data set is only somewhat correlated with
the total number of k-mers.** Trimming protocols, sequencing depth,
and polymorphism rates are all important factors that affect k-mer
count.

The bad news is that we don't have good ways to estimate total k-mer
count a priori, although we can give you some rules of thumb, below.
In fact, counting the total number of distinct k-mers is a somewhat
annoying challenge.  Frankly, we recommend *just guessing* instead of
trying to be all scientific about it.

The good news is that you can never give khmer too much memory!  k-mer
counting and set membership simply gets more and more accurate as you
feed it more memory.  (Although there may be performance hits from
memory I/O, e.g.  `see the NUMA architecture
<http://en.wikipedia.org/wiki/Non-Uniform_Memory_Access>`__.)  The
other good news is that khmer can measure the false positive rate and
detect dangerously low memory conditions.  For partitioning, we
actually *know* what a too-high false positive rate is -- our `k-mer
percolation paper <http://arxiv.org/abs/1112.4193>`__ lays out the
math.  For digital normalization, we assume that a false positive rate
of 10% is bad.  In both cases the data-loading scripts will exit with
an error-code.

Rules of thumb
--------------

For digital normalization, we recommend:

 - ``-M 8e9`` for any amount of sequencing for a single microbial genome,
   MDA-amplified or single colony.

 - ``-M 16e9`` for up to a billion mRNAseq reads from any organism.  Past that,
   increase it.

 - ``-M 32e9`` for most eukaryotic genome samples.

 - ``-M 32e9`` will also handle most "simple" metagenomic samples (HMP on down)

 - For metagenomic samples that are more complex, such as soil or marine,
   start as high as possible.  For example, we are using ``-M 256e9`` for
   ~300 Gbp of soil reads.

For partitioning of complex metagenome samples, we recommend starting
as high as you can -- something like half your system memory.  So if
you have 256 GB of RAM, use ``-M 128e9`` which will use 128 GB of RAM
for the basic graph storage, leaving other memory for the ancillary
data structures.
