#
# This file is part of khmer, https://github.com/dib-lab/khmer/, and is
# Copyright (C) Michigan State University, 2009-2015. It is licensed under
# the three-clause BSD license; see LICENSE.
# Contact: khmer-project@idyll.org
#
# pylint: disable=missing-docstring,protected-access,no-member,

from __future__ import print_function
from __future__ import absolute_import

import khmer
from khmer import ReadParser

import screed

from . import khmer_tst_utils as utils
from nose.plugins.attrib import attr


def teardown():
    utils.cleanup()


@attr('huge')
def test_toobig():
    try:
        pt = khmer.Nodegraph(32, 1e13, 1)
        assert 0, "This should fail"
    except MemoryError as err:
        print(str(err))


def test__get_set_tag_density():
    nodegraph = khmer._Nodegraph(32, [1])

    orig = nodegraph._get_tag_density()
    assert orig != 2
    nodegraph._set_tag_density(2)
    assert nodegraph._get_tag_density() == 2


def test_update_from():
    nodegraph = khmer.Nodegraph(5, 1000, 4)
    other_nodegraph = khmer.Nodegraph(5, 1000, 4)

    assert nodegraph.get('AAAAA') == 0
    assert nodegraph.get('GCGCG') == 0
    assert other_nodegraph.get('AAAAA') == 0
    assert other_nodegraph.get('GCGCG') == 0

    other_nodegraph.count('AAAAA')

    assert nodegraph.get('AAAAA') == 0
    assert nodegraph.get('GCGCG') == 0
    assert other_nodegraph.get('AAAAA') == 1
    assert other_nodegraph.get('GCGCG') == 0

    nodegraph.count('GCGCG')

    assert nodegraph.get('AAAAA') == 0
    assert nodegraph.get('GCGCG') == 1
    assert other_nodegraph.get('AAAAA') == 1
    assert other_nodegraph.get('GCGCG') == 0

    nodegraph.update(other_nodegraph)

    assert nodegraph.get('AAAAA') == 1
    assert nodegraph.get('GCGCG') == 1
    assert other_nodegraph.get('AAAAA') == 1
    assert other_nodegraph.get('GCGCG') == 0


def test_update_from_diff_ksize_2():
    nodegraph = khmer.Nodegraph(5, 1000, 4)
    other_nodegraph = khmer.Nodegraph(4, 1000, 4)

    try:
        nodegraph.update(other_nodegraph)
        assert 0, "should not be reached"
    except ValueError as err:
        print(str(err))

    try:
        other_nodegraph.update(nodegraph)
        assert 0, "should not be reached"
    except ValueError as err:
        print(str(err))


def test_update_from_diff_tablesize():
    nodegraph = khmer.Nodegraph(5, 100, 4)
    other_nodegraph = khmer.Nodegraph(5, 1000, 4)

    try:
        nodegraph.update(other_nodegraph)
        assert 0, "should not be reached"
    except ValueError as err:
        print(str(err))


def test_update_from_diff_num_tables():
    nodegraph = khmer.Nodegraph(5, 1000, 3)
    other_nodegraph = khmer.Nodegraph(5, 1000, 4)

    try:
        nodegraph.update(other_nodegraph)
        assert 0, "should not be reached"
    except ValueError as err:
        print(str(err))


def test_n_occupied_1():
    filename = utils.get_test_data('random-20-a.fa')

    ksize = 20  # size of kmer
    htable_size = 100000  # size of hashtable
    num_nodegraphs = 1  # number of hashtables

    # test modified c++ n_occupied code
    nodegraph = khmer.Nodegraph(ksize, htable_size, num_nodegraphs)

    for _, record in enumerate(screed.open(filename)):
        nodegraph.consume(record.sequence)

    # this number calculated independently
    assert nodegraph.n_occupied() == 3884, nodegraph.n_occupied()


def test_bloom_python_1():
    # test python code to count unique kmers using bloom filter
    filename = utils.get_test_data('random-20-a.fa')

    ksize = 20  # size of kmer
    htable_size = 100000  # size of hashtable
    num_nodegraphs = 3  # number of hashtables

    nodegraph = khmer.Nodegraph(ksize, htable_size, num_nodegraphs)

    n_unique = 0
    for _, record in enumerate(screed.open(filename)):
        sequence = record.sequence
        seq_len = len(sequence)
        for n in range(0, seq_len + 1 - ksize):
            kmer = sequence[n:n + ksize]
            if not nodegraph.get(kmer):
                n_unique += 1
            nodegraph.count(kmer)

    assert n_unique == 3960
    assert nodegraph.n_occupied() == 3884, nodegraph.n_occupied()

    # this number equals n_unique
    assert nodegraph.n_unique_kmers() == 3960, nodegraph.n_unique_kmers()


def test_bloom_c_1():
    # test c++ code to count unique kmers using bloom filter

    filename = utils.get_test_data('random-20-a.fa')

    ksize = 20  # size of kmer
    htable_size = 100000  # size of hashtable
    num_nodegraphs = 3  # number of hashtables

    nodegraph = khmer.Nodegraph(ksize, htable_size, num_nodegraphs)

    for _, record in enumerate(screed.open(filename)):
        nodegraph.consume(record.sequence)

    assert nodegraph.n_occupied() == 3884
    assert nodegraph.n_unique_kmers() == 3960


def test_n_occupied_2():  # simple one
    ksize = 4
    htable_size = 10  # use 11
    num_nodegraphs = 1

    nodegraph = khmer._Nodegraph(ksize, [11])
    nodegraph.count('AAAA')  # 00 00 00 00 = 0
    assert nodegraph.n_occupied() == 1

    nodegraph.count('ACTG')  # 00 10 01 11 =
    assert nodegraph.n_occupied() == 2

    nodegraph.count('AACG')  # 00 00 10 11 = 11  # collision 1

    assert nodegraph.n_occupied() == 2
    nodegraph.count('AGAC')   # 00  11 00 10 # collision 2
    assert nodegraph.n_occupied() == 2, nodegraph.n_occupied()


def test_bloom_c_2():  # simple one
    ksize = 4

    # use only 1 hashtable, no bloom filter
    nodegraph = khmer._Nodegraph(ksize, [11])
    nodegraph.count('AAAA')  # 00 00 00 00 = 0
    nodegraph.count('ACTG')  # 00 10 01 11 =
    assert nodegraph.n_unique_kmers() == 2
    nodegraph.count('AACG')  # 00 00 10 11 = 11  # collision  with 1st kmer
    assert nodegraph.n_unique_kmers() == 2
    nodegraph.count('AGAC')   # 00  11 00 10 # collision  with 2nd kmer
    assert nodegraph.n_unique_kmers() == 2

    # use two hashtables with 11,13
    other_nodegraph = khmer._Nodegraph(ksize, [11, 13])
    other_nodegraph.count('AAAA')  # 00 00 00 00 = 0

    other_nodegraph.count('ACTG')  # 00 10 01 11 = 2*16 +4 +3 = 39
    assert other_nodegraph.n_unique_kmers() == 2
    # 00 00 10 11 = 11  # collision with only 1st kmer
    other_nodegraph.count('AACG')
    assert other_nodegraph.n_unique_kmers() == 3
    other_nodegraph.count('AGAC')
    # 00  11 00 10  3*16 +2 = 50
    # collision with both 2nd and 3rd kmers

    assert other_nodegraph.n_unique_kmers() == 3


def test_filter_if_present():
    nodegraph = khmer._Nodegraph(32, [3, 5])

    maskfile = utils.get_test_data('filter-test-A.fa')
    inputfile = utils.get_test_data('filter-test-B.fa')
    outfile = utils.get_temp_filename('filter')

    nodegraph.consume_fasta(maskfile)
    nodegraph.filter_if_present(inputfile, outfile)

    records = list(screed.open(outfile))
    assert len(records) == 1
    assert records[0]['name'] == '3'


def test_combine_pe():
    inpfile = utils.get_test_data('combine_parts_1.fa')
    nodegraph = khmer._Nodegraph(32, [1])

    nodegraph.consume_partitioned_fasta(inpfile)
    assert nodegraph.count_partitions() == (2, 0)

    first_seq = "CATGCAGAAGTTCCGCAACCATACCGTTCAGT"
    pid1 = nodegraph.get_partition_id(first_seq)

    second_seq = "CAAATGTACATGCACTTAAAATCATCCAGCCG"
    pid2 = nodegraph.get_partition_id(second_seq)

    assert pid1 == 2
    assert pid2 == 80293

    nodegraph.join_partitions(pid1, pid2)

    pid1 = nodegraph.get_partition_id(first_seq)
    pid2 = nodegraph.get_partition_id(second_seq)

    assert pid1 == pid2
    assert nodegraph.count_partitions() == (1, 0)


def test_load_partitioned():
    inpfile = utils.get_test_data('combine_parts_1.fa')
    nodegraph = khmer._Nodegraph(32, [1])

    nodegraph.consume_partitioned_fasta(inpfile)
    assert nodegraph.count_partitions() == (2, 0)

    first_seq = "CATGCAGAAGTTCCGCAACCATACCGTTCAGT"
    assert nodegraph.get(first_seq)

    second_seq = "CAAATGTACATGCACTTAAAATCATCCAGCCG"
    assert nodegraph.get(second_seq)

    third_s = "CATGCAGAAGTTCCGCAACCATACCGTTCAGTTCCTGGTGGCTA"[-32:]
    assert nodegraph.get(third_s)


def test_count_within_radius_simple():
    inpfile = utils.get_test_data('all-A.fa')
    nodegraph = khmer._Nodegraph(4, [3, 5])

    print(nodegraph.consume_fasta(inpfile))
    n = nodegraph.count_kmers_within_radius('AAAA', 1)
    assert n == 1

    n = nodegraph.count_kmers_within_radius('AAAA', 10)
    assert n == 1


def test_count_within_radius_big():
    inpfile = utils.get_test_data('random-20-a.fa')
    nodegraph = khmer.Nodegraph(20, 1e5, 4)

    nodegraph.consume_fasta(inpfile)
    n = nodegraph.count_kmers_within_radius('CGCAGGCTGGATTCTAGAGG', int(1e6))
    assert n == 3961, n

    nodegraph = khmer.Nodegraph(21, 1e5, 4)
    nodegraph.consume_fasta(inpfile)
    n = nodegraph.count_kmers_within_radius('CGCAGGCTGGATTCTAGAGGC', int(1e6))
    assert n == 39


def test_count_kmer_degree():
    inpfile = utils.get_test_data('all-A.fa')
    nodegraph = khmer._Nodegraph(4, [3, 5])
    nodegraph.consume_fasta(inpfile)

    assert nodegraph.kmer_degree('AAAA') == 2
    assert nodegraph.kmer_degree('AAAT') == 1
    assert nodegraph.kmer_degree('AATA') == 0
    assert nodegraph.kmer_degree('TAAA') == 1


def test_save_load_tagset():
    nodegraph = khmer._Nodegraph(32, [1])

    outfile = utils.get_temp_filename('tagset')

    nodegraph.add_tag('A' * 32)
    nodegraph.save_tagset(outfile)

    nodegraph.add_tag('G' * 32)

    nodegraph.load_tagset(outfile)              # implicitly => clear_tags=True
    nodegraph.save_tagset(outfile)

    # if tags have been cleared, then the new tagfile will be larger (34 bytes)
    # else smaller (26 bytes).

    fp = open(outfile, 'rb')
    data = fp.read()
    fp.close()
    assert len(data) == 30, len(data)


def test_save_load_tagset_noclear():
    nodegraph = khmer._Nodegraph(32, [1])

    outfile = utils.get_temp_filename('tagset')

    nodegraph.add_tag('A' * 32)
    nodegraph.save_tagset(outfile)

    nodegraph.add_tag('G' * 32)

    nodegraph.load_tagset(outfile, False)  # set clear_tags => False; zero tags
    nodegraph.save_tagset(outfile)

    # if tags have been cleared, then the new tagfile will be large (34 bytes);
    # else small (26 bytes).

    fp = open(outfile, 'rb')
    data = fp.read()
    fp.close()
    assert len(data) == 38, len(data)


def test_stop_traverse():
    filename = utils.get_test_data('random-20-a.fa')

    ksize = 20  # size of kmer
    htable_size = 1e4  # size of hashtable
    num_nodegraphs = 3  # number of hashtables

    nodegraph = khmer.Nodegraph(ksize, htable_size, num_nodegraphs)

    # without tagging/joining across consume, this breaks into two partition;
    # with, it is one partition.
    nodegraph.add_stop_tag('TTGCATACGTTGAGCCAGCG')

    # DO NOT join reads across stoptags
    nodegraph.consume_fasta_and_tag(filename)
    subset = nodegraph.do_subset_partition(0, 0, True)
    nodegraph.merge_subset(subset)

    n, _ = nodegraph.count_partitions()
    assert n == 2, n


def test_tag_across_stoptraverse():
    filename = utils.get_test_data('random-20-a.fa')

    ksize = 20  # size of kmer
    htable_size = 1e4  # size of hashtable
    num_nodegraphs = 3  # number of hashtables

    nodegraph = khmer.Nodegraph(ksize, htable_size, num_nodegraphs)

    # without tagging/joining across consume, this breaks into two partition;
    # with, it is one partition.
    nodegraph.add_stop_tag('CCGAATATATAACAGCGACG')

    # DO join reads across
    nodegraph.consume_fasta_and_tag_with_stoptags(filename)
    subset = nodegraph.do_subset_partition(0, 0)
    n, _ = nodegraph.count_partitions()
    assert n == 99                       # reads only connected by traversal...

    n, _ = nodegraph.subset_count_partitions(subset)
    assert n == 2                        # but need main to cross stoptags.

    nodegraph.merge_subset(subset)

    n, _ = nodegraph.count_partitions()         # ta-da!
    assert n == 1, n


def test_notag_across_stoptraverse():
    filename = utils.get_test_data('random-20-a.fa')

    ksize = 20  # size of kmer
    htable_size = 1e4  # size of hashtable
    num_nodegraphs = 3  # number of hashtables

    nodegraph = khmer.Nodegraph(ksize, htable_size, num_nodegraphs)

    # connecting k-mer at the beginning/end of a read: breaks up into two.
    nodegraph.add_stop_tag('TTGCATACGTTGAGCCAGCG')

    nodegraph.consume_fasta_and_tag_with_stoptags(filename)

    subset = nodegraph.do_subset_partition(0, 0)
    nodegraph.merge_subset(subset)

    n, _ = nodegraph.count_partitions()
    assert n == 2, n


def test_find_stoptags():
    nodegraph = khmer._Nodegraph(5, [1])
    nodegraph.add_stop_tag("AAAAA")

    assert nodegraph.identify_stoptags_by_position("AAAAA") == [0]
    assert nodegraph.identify_stoptags_by_position("AAAAAA") == [0, 1]
    assert nodegraph.identify_stoptags_by_position("TTTTT") == [0]
    assert nodegraph.identify_stoptags_by_position("TTTTTT") == [0, 1]


def test_find_stoptagsecond_seq():
    nodegraph = khmer._Nodegraph(4, [1])
    nodegraph.add_stop_tag("ATGC")

    x = nodegraph.identify_stoptags_by_position("ATGCATGCGCAT")
    assert x == [0, 2, 4, 8], x


def test_get_ksize():
    kh = khmer._Nodegraph(22, [1])
    assert kh.ksize() == 22


def test_get_hashsizes():
    kh = khmer.Nodegraph(22, 100, 4)
    # Py2/3 hack, longify converts to long in py2, remove once py2 isn't
    # supported any longer.
    expected = utils.longify([97, 89, 83, 79])
    assert kh.hashsizes() == expected, kh.hashsizes()


def test_extract_unique_paths_0():
    kh = khmer._Nodegraph(10, [5, 7, 11, 13])

    x = kh.extract_unique_paths('ATGGAGAGACACAGATAGACAGGAGTGGCGATG', 10, 1)
    assert x == ['ATGGAGAGACACAGATAGACAGGAGTGGCGATG']

    kh.consume('ATGGAGAGACACAGATAGACAGGAGTGGCGATG')
    x = kh.extract_unique_paths('ATGGAGAGACACAGATAGACAGGAGTGGCGATG', 10, 1)
    assert not x


def test_extract_unique_paths_1():
    kh = khmer._Nodegraph(10, [5, 7, 11, 13])

    kh.consume('AGTGGCGATG')
    x = kh.extract_unique_paths('ATGGAGAGACACAGATAGACAGGAGTGGCGATG', 10, 1)
    print(x)
    assert x == ['ATGGAGAGACACAGATAGACAGGAGTGGCGAT']  # all but the last k-mer


def test_extract_unique_paths_2():
    kh = khmer._Nodegraph(10, [5, 7, 11, 13])

    kh.consume('ATGGAGAGAC')
    x = kh.extract_unique_paths('ATGGAGAGACACAGATAGACAGGAGTGGCGATG', 10, 1)
    print(x)
    assert x == ['TGGAGAGACACAGATAGACAGGAGTGGCGATG']  # all but the 1st k-mer


def test_extract_unique_paths_3():
    kh = khmer._Nodegraph(10, [5, 7, 11, 13])

    kh.consume('ATGGAGAGAC')
    kh.consume('AGTGGCGATG')
    x = kh.extract_unique_paths('ATGGAGAGACACAGATAGACAGGAGTGGCGATG', 10, 1)
    print(x)
    # all but the 1st/last k-mer
    assert x == ['TGGAGAGACACAGATAGACAGGAGTGGCGAT']


def test_extract_unique_paths_4():
    kh = khmer.Nodegraph(10, 1e6, 4)

    kh.consume('ATGGAGAGAC')
    kh.consume('AGTGGCGATG')

    kh.consume('ATAGACAGGA')

    x = kh.extract_unique_paths('ATGGAGAGACACAGATAGACAGGAGTGGCGATG', 10, 1)
    print(x)
    assert x == ['TGGAGAGACACAGATAGACAGG', 'TAGACAGGAGTGGCGAT']


def test_find_unpart():
    filename = utils.get_test_data('random-20-a.odd.fa')
    filename2 = utils.get_test_data('random-20-a.even.fa')

    ksize = 20  # size of kmer
    htable_size = 1e4  # size of hashtable
    num_nodegraphs = 3  # number of hashtables

    nodegraph = khmer.Nodegraph(ksize, htable_size, num_nodegraphs)
    nodegraph.consume_fasta_and_tag(filename)

    subset = nodegraph.do_subset_partition(0, 0)
    nodegraph.merge_subset(subset)

    n, _ = nodegraph.count_partitions()
    assert n == 49

    nodegraph.find_unpart(filename2, True, False)
    n, _ = nodegraph.count_partitions()
    assert n == 1, n                     # all sequences connect


def test_find_unpart_notraverse():
    filename = utils.get_test_data('random-20-a.odd.fa')
    filename2 = utils.get_test_data('random-20-a.even.fa')

    ksize = 20  # size of kmer
    htable_size = 1e4  # size of hashtable
    num_nodegraphs = 3  # number of hashtables

    nodegraph = khmer.Nodegraph(ksize, htable_size, num_nodegraphs)
    nodegraph.consume_fasta_and_tag(filename)

    subset = nodegraph.do_subset_partition(0, 0)
    nodegraph.merge_subset(subset)

    n, _ = nodegraph.count_partitions()
    assert n == 49

    nodegraph.find_unpart(filename2, False, False)     # <-- don't traverse
    n, _ = nodegraph.count_partitions()
    assert n == 99, n                    # all sequences disconnected


def test_find_unpart_fail():
    filename = utils.get_test_data('random-20-a.odd.fa')
    filename2 = utils.get_test_data('random-20-a.odd.fa')  # <- switch to odd

    ksize = 20  # size of kmer
    htable_size = 1e4  # size of hashtable
    num_nodegraphs = 3  # number of hashtables

    nodegraph = khmer.Nodegraph(ksize, htable_size, num_nodegraphs)
    nodegraph.consume_fasta_and_tag(filename)

    subset = nodegraph.do_subset_partition(0, 0)
    nodegraph.merge_subset(subset)

    n, _ = nodegraph.count_partitions()
    assert n == 49

    nodegraph.find_unpart(filename2, True, False)
    n, _ = nodegraph.count_partitions()
    assert n == 49, n                    # only 49 sequences worth of tags


def test_simple_median():
    hi = khmer.Nodegraph(6, 1e5, 2)

    (median, average, stddev) = hi.get_median_count("AAAAAA")
    print(median, average, stddev)
    assert median == 0
    assert average == 0.0
    assert stddev == 0.0

    hi.consume("AAAAAA")
    (median, average, stddev) = hi.get_median_count("AAAAAA")
    print(median, average, stddev)
    assert median == 1
    assert average == 1.0
    assert stddev == 0.0


def test_badget():
    hbts = khmer.Nodegraph(6, 1e6, 1)

    dna = "AGCTTTTCATTCTGACTGCAACGGGCAATATGTCTCTGTGTGGATTAAAAAAAGAGTGTCTGATAG"

    hbts.consume(dna)

    assert hbts.get("AGCTTT") == 1

    assert hbts.get("GATGAG") == 0

    try:
        hbts.get(b"AGCTT")
        assert 0, "this should fail"
    except ValueError as err:
        print(str(err))

    try:
        hbts.get(u"AGCTT")
        assert 0, "this should fail"
    except ValueError as err:
        print(str(err))


#


def test_load_notexist_should_fail():
    savepath = utils.get_temp_filename('tempnodegraphsave0.htable')

    hi = khmer._Countgraph(12, [1])
    try:
        hi.load(savepath)
        assert 0, "load should fail"
    except OSError:
        pass


def test_load_truncated_should_fail():
    inpath = utils.get_test_data('random-20-a.fa')
    savepath = utils.get_temp_filename('tempnodegraphsave0.ct')

    hi = khmer.Countgraph(12, 1000, 2)

    hi.consume_fasta(inpath)
    hi.save(savepath)

    fp = open(savepath, 'rb')
    data = fp.read()
    fp.close()

    fp = open(savepath, 'wb')
    fp.write(data[:1000])
    fp.close()

    hi = khmer._Countgraph(12, [1])
    try:
        hi.load(savepath)
        assert 0, "load should fail"
    except OSError as e:
        print(str(e))


def test_save_load_tagset_notexist():
    nodegraph = khmer._Nodegraph(32, [1])

    outfile = utils.get_temp_filename('tagset')
    try:
        nodegraph.load_tagset(outfile)
        assert 0, "this test should fail"
    except OSError as e:
        print(str(e))


def test_save_load_tagset_trunc():
    nodegraph = khmer._Nodegraph(32, [1])

    outfile = utils.get_temp_filename('tagset')

    nodegraph.add_tag('A' * 32)
    nodegraph.add_tag('G' * 32)
    nodegraph.save_tagset(outfile)

    # truncate tagset file...
    fp = open(outfile, 'rb')
    data = fp.read()
    fp.close()

    for i in range(len(data)):
        fp = open(outfile, 'wb')
        fp.write(data[:i])
        fp.close()

        # try loading it...
        try:
            nodegraph.load_tagset(outfile)
            assert 0, "this test should fail"
        except OSError as err:
            print(str(err), i)

    # try loading it...
    try:
        nodegraph.load_tagset(outfile)
        assert 0, "this test should fail"
    except OSError:
        pass

# to build the test files used below, add 'test' to this function
# and then look in /tmp. You will need to tweak the version info in
# khmer.hh in order to create "bad" versions, of course. -CTB


def _build_testfiles():
    # nodegraph file

    inpath = utils.get_test_data('random-20-a.fa')
    hi = khmer.Nodegraph(12, 2)
    hi.consume_fasta(inpath)
    hi.save('/tmp/goodversion-k12.htable')

    # tagset file

    nodegraph = khmer._Nodegraph(32, [1])

    nodegraph.add_tag('A' * 32)
    nodegraph.add_tag('G' * 32)
    nodegraph.save_tagset('/tmp/goodversion-k32.tagset')

    # stoptags file

    fakelump_fa = utils.get_test_data('fakelump.fa')

    nodegraph = khmer.Nodegraph(32, 4, 4)
    nodegraph.consume_fasta_and_tag(fakelump_fa)

    subset = nodegraph.do_subset_partition(0, 0)
    nodegraph.merge_subset(subset)

    EXCURSION_DISTANCE = 40
    EXCURSION_KMER_THRESHOLD = 82
    EXCURSION_KMER_COUNT_THRESHOLD = 1
    counting = khmer.Countgraph(32, 4, 4)

    nodegraph.repartition_largest_partition(None, counting,
                                            EXCURSION_DISTANCE,
                                            EXCURSION_KMER_THRESHOLD,
                                            EXCURSION_KMER_COUNT_THRESHOLD)

    nodegraph.save_stop_tags('/tmp/goodversion-k32.stoptags')


def test_hashbits_file_version_check():
    nodegraph = khmer._Nodegraph(12, [1])

    inpath = utils.get_test_data('badversion-k12.htable')

    try:
        nodegraph.load(inpath)
        assert 0, "this should fail"
    except OSError as e:
        print(str(e))


def test_nodegraph_file_type_check():
    kh = khmer._Countgraph(12, [1])
    savepath = utils.get_temp_filename('tempcountingsave0.ct')
    kh.save(savepath)

    nodegraph = khmer._Nodegraph(12, [1])

    try:
        nodegraph.load(savepath)
        assert 0, "this should fail"
    except OSError as e:
        print(str(e))


def test_stoptags_file_version_check():
    nodegraph = khmer._Nodegraph(32, [1])

    inpath = utils.get_test_data('badversion-k32.stoptags')

    try:
        nodegraph.load_stop_tags(inpath)
        assert 0, "this should fail"
    except OSError as e:
        print(str(e))


def test_stoptags_ksize_check():
    nodegraph = khmer._Nodegraph(31, [1])

    inpath = utils.get_test_data('goodversion-k32.stoptags')
    try:
        nodegraph.load_stop_tags(inpath)
        assert 0, "this should fail"
    except OSError as e:
        print(str(e))


def test_stop_tags_filetype_check():
    nodegraph = khmer._Nodegraph(31, [1])

    inpath = utils.get_test_data('goodversion-k32.tagset')
    try:
        nodegraph.load_stop_tags(inpath)
        assert 0, "this should fail"
    except OSError as e:
        print(str(e))


def test_tagset_file_version_check():
    nodegraph = khmer._Nodegraph(32, [1])

    inpath = utils.get_test_data('badversion-k32.tagset')

    try:
        nodegraph.load_tagset(inpath)
        assert 0, "this should fail"
    except OSError as e:
        print(str(e))


def test_stop_tags_truncate_check():
    nodegraph = khmer._Nodegraph(32, [1])

    inpath = utils.get_test_data('goodversion-k32.tagset')
    data = open(inpath, 'rb').read()

    truncpath = utils.get_temp_filename('zzz')
    for i in range(len(data)):
        fp = open(truncpath, 'wb')
        fp.write(data[:i])
        fp.close()

        try:
            nodegraph.load_stop_tags(truncpath)
            assert 0, "expect failure of previous command"
        except OSError as e:
            print(i, str(e))


def test_tagset_ksize_check():
    nodegraph = khmer._Nodegraph(31, [1])

    inpath = utils.get_test_data('goodversion-k32.tagset')
    try:
        nodegraph.load_tagset(inpath)
        assert 0, "this should fail"
    except OSError as e:
        print(str(e))


def test_tagset_filetype_check():
    nodegraph = khmer._Nodegraph(31, [1])

    inpath = utils.get_test_data('goodversion-k32.stoptags')
    try:
        nodegraph.load_tagset(inpath)
        assert 0, "this should fail"
    except OSError as e:
        print(str(e))


def test_bad_primes_list():
    try:
        coutingtable = khmer._Nodegraph(31, ["a", "b", "c"], 1)
        assert 0, "Bad primes list should fail"
    except TypeError as e:
        print(str(e))


def test_consume_absentfasta_with_reads_parser():
    nodegraph = khmer._Nodegraph(31, [1])
    try:
        nodegraph.consume_fasta_with_reads_parser()
        assert 0, "this should fail"
    except TypeError as err:
        print(str(err))
    try:
        readparser = ReadParser(utils.get_test_data('empty-file'))
        nodegraph.consume_fasta_with_reads_parser(readparser)
        assert 0, "this should fail"
    except OSError as err:
        print(str(err))
    except ValueError as err:
        print(str(err))


def test_bad_primes():
    try:
        countgraph = khmer._Nodegraph.__new__(
            khmer._Nodegraph, 6, ["a", "b", "c"])
        assert 0, "this should fail"
    except TypeError as e:
        print(str(e))


def test_consume_fasta_and_tag_with_badreads_parser():
    nodegraph = khmer.Nodegraph(6, 1e6, 2)
    try:
        readsparser = khmer.ReadParser(utils.get_test_data("test-empty.fa"))
        nodegraph.consume_fasta_and_tag_with_reads_parser(readsparser)
        assert 0, "this should fail"
    except OSError as e:
        print(str(e))
    except ValueError as e:
        print(str(e))


def test_n_occupied_save_load():
    filename = utils.get_test_data('random-20-a.fa')

    nodegraph = khmer.Nodegraph(20, 100000, 3)

    for _, record in enumerate(screed.open(filename)):
        nodegraph.consume(record.sequence)

    assert nodegraph.n_occupied() == 3884
    assert nodegraph.n_unique_kmers() == 3960

    savefile = utils.get_temp_filename('out')
    nodegraph.save(savefile)

    ng2 = khmer.load_nodegraph(savefile)
    assert ng2.n_occupied() == 3884, ng2.n_occupied()
    assert ng2.n_unique_kmers() == 0    # this is intended behavior, sigh.


def test_n_occupied_vs_countgraph():
    filename = utils.get_test_data('random-20-a.fa')

    nodegraph = khmer.Nodegraph(20, 100000, 3)
    countgraph = khmer.Countgraph(20, 100000, 3)

    assert nodegraph.n_occupied() == 0, nodegraph.n_occupied()
    assert countgraph.n_occupied() == 0, countgraph.n_occupied()

    assert nodegraph.n_unique_kmers() == 0, nodegraph.n_unique_kmers()
    assert countgraph.n_unique_kmers() == 0, countgraph.n_unique_kmers()

    for n, record in enumerate(screed.open(filename)):
        nodegraph.consume(record.sequence)
        countgraph.consume(record.sequence)

    assert nodegraph.hashsizes() == nodegraph.hashsizes()

    # these are all the same -- good :).
    assert nodegraph.n_occupied() == 3884, nodegraph.n_occupied()
    assert countgraph.n_occupied() == 3884, countgraph.n_occupied()

    assert nodegraph.n_unique_kmers() == 3960, nodegraph.n_unique_kmers()
    assert countgraph.n_unique_kmers() == 3960, countgraph.n_unique_kmers()


def test_n_occupied_vs_countgraph_another_size():
    filename = utils.get_test_data('random-20-a.fa')

    nodegraph = khmer.Nodegraph(20, 10000, 3)
    countgraph = khmer.Countgraph(20, 10000, 3)

    assert nodegraph.n_occupied() == 0, nodegraph.n_occupied()
    assert countgraph.n_occupied() == 0, countgraph.n_occupied()

    assert nodegraph.n_unique_kmers() == 0, nodegraph.n_unique_kmers()
    assert countgraph.n_unique_kmers() == 0, countgraph.n_unique_kmers()

    for n, record in enumerate(screed.open(filename)):
        nodegraph.consume(record.sequence)
        countgraph.consume(record.sequence)

    assert nodegraph.hashsizes() == nodegraph.hashsizes()

    # these are all the same -- good :).
    assert nodegraph.n_occupied() == 3269, nodegraph.n_occupied()
    assert countgraph.n_occupied() == 3269, countgraph.n_occupied()

    assert nodegraph.n_unique_kmers() == 3916, nodegraph.n_unique_kmers()
    assert countgraph.n_unique_kmers() == 3916, countgraph.n_unique_kmers()
