.. vim: set filetype=rst

==============================
khmer's command-line interface
==============================

The simplest way to use khmer's functionality is through the command
line scripts, located in the scripts/ directory of the khmer
distribution.  Below is our documentation for these scripts.  Note
that all scripts can be given :option:`-h` which will print out
a list of arguments taken by that script.

Scripts that use k-mer counting tables or k-mer graphs take an
:option:`-M` parameter, which sets the maximum memory usage in bytes.
This should generally be set as high as possible; see
:doc:`choosing-table-sizes` for more information.

1. :ref:`scripts-counting`
2. :ref:`scripts-partitioning`
3. :ref:`scripts-diginorm`
4. :ref:`scripts-read-handling`

.. note::
 
   Almost all scripts take in either FASTA and FASTQ format, and
   output the same.  Some scripts may only recognize FASTQ if the file
   ending is '.fq' or '.fastq', at least for now.

   Files ending with '.gz' will be treated as gzipped files, and
   files ending with '.bz2' will be treated as bzip2'd files.

.. _scripts-counting:

k-mer counting and abundance filtering
======================================

.. autoprogram:: load-into-counting:get_parser()
        :prog: load-into-counting.py

.. autoprogram:: abundance-dist:get_parser()
        :prog: abundance-dist.py

.. autoprogram:: abundance-dist-single:get_parser()
        :prog: abundance-dist-single.py

.. autoprogram:: filter-abund:get_parser()
        :prog: filter-abund.py

.. autoprogram:: filter-abund-single:get_parser()
        :prog: filter-abund-single.py

.. autoprogram:: trim-low-abund:get_parser()
        :prog: trim-low-abund.py

.. autoprogram:: count-median:get_parser()
        :prog: count-median.py

.. autoprogram:: unique-kmers:get_parser()
        :prog: unique-kmers.py

.. _scripts-partitioning:

Partitioning
============

.. autoprogram:: do-partition:get_parser()
        :prog: do-partition.py

.. autoprogram:: load-graph:get_parser()
        :prog: load-graph.py

See :program:`extract-partitions.py` for a complete workflow.

.. autoprogram:: partition-graph:get_parser()
        :prog: partition-graph.py

See 'Artifact removal' to understand the stoptags argument.

.. autoprogram:: merge-partitions:get_parser()
        :prog: merge-partition.py

.. autoprogram:: annotate-partitions:get_parser()
        :prog: annotate-partitions.py

.. autoprogram:: extract-partitions:get_parser()
        :prog: extract-partitions.py
 
Artifact removal
----------------

The following scripts are specialized scripts for finding and removing
highly-connected k-mers (HCKs).  See :doc:`partitioning-big-data`.

.. autoprogram:: make-initial-stoptags:get_parser()
        :prog: make-initial-stoptags.py

.. autoprogram:: find-knots:get_parser()
        :prog: find-knots.py

.. autoprogram:: filter-stoptags:get_parser()
        :prog: filter-stoptags.py

.. _scripts-diginorm:

Digital normalization
=====================

.. autoprogram:: normalize-by-median:get_parser()
        :prog: normalize-by-median.py

.. _scripts-read-handling:

Read handling: interleaving, splitting, etc.
============================================

.. autoprogram:: extract-long-sequences:get_parser()
        :prog: extract-long-sequences.py

.. autoprogram:: extract-paired-reads:get_parser()
        :prog: extract-paired-reads.py

.. autoprogram:: fastq-to-fasta:get_parser()
        :prog: fastq-to-fasta.py

.. autoprogram:: interleave-reads:get_parser()
        :prog: interleave-reads.py

.. autoprogram:: readstats:get_parser()
        :prog: readstats.py

.. autoprogram:: sample-reads-randomly:get_parser()
        :prog: sample-reads-randomly.py

.. autoprogram:: split-paired-reads:get_parser()
        :prog: split-paired-reads.py
