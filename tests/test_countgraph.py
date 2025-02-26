from __future__ import print_function
from __future__ import absolute_import, unicode_literals
#
# This file is part of khmer, https://github.com/dib-lab/khmer/, and is
# Copyright (C) Michigan State University, 2009-2015. It is licensed under
# the three-clause BSD license; see LICENSE.
# Contact: khmer-project@idyll.org
#
# pylint: disable=missing-docstring,protected-access
import gzip

import os
import shutil

import khmer
from . import khmer_tst_utils as utils
from khmer import ReadParser
import screed

import nose
from nose.plugins.attrib import attr
from nose.tools import assert_raises


MAX_COUNT = 255
MAX_BIGCOUNT = 65535

# from http://www.rsok.com/~jrm/printprimes.html
PRIMES_1m = [1000003, 1009837]
PRIMES_100m = [100009979, 100000007]
PRIMES_1b = [1000000007, 1000000919]
PRIMES_2b = [1999999973, 1999999943]
PRIMES_4b = [4000000007, 4000000009]
PRIMES_8b = [8000000011, 8000000051]

DNA = "AGCTTTTCATTCTGACTGCAACGGGCAATATGTCTCTGTGTGGATTAAAAAAAGAGTGTCTGATAGCAGC"


def teardown():
    utils.cleanup()


class Test_Countgraph(object):

    def setup(self):
        self.hi = khmer._Countgraph(12, PRIMES_1m)

    def test_failed_get(self):
        GG = 'G' * 12                   # forward_hash: 11184810
        GGhash = khmer.forward_hash(GG, 12)
        assert khmer.forward_hash(GG, 12) == 11184810

        hi = self.hi
        hi.consume(GG)

        try:
            hi.get(float(GGhash))
            assert "the previous statement should fail"
        except ValueError as err:
            print(str(err))

    def test_collision_1(self):

        GG = 'G' * 12                   # forward_hash: 11184810
        GGhash = khmer.forward_hash(GG, 12)
        assert khmer.forward_hash(GG, 12) == 11184810

        collision_1 = 'AAACGTATGACT'
        assert khmer.forward_hash(collision_1, 12) == 184777

        collision_2 = 'AAATACCGAGCG'
        assert khmer.forward_hash(collision_2, 12) == 76603

        # note, hash(GG) % 1000003 == hash(collision_1)
        # note, hash(GG) % 1009837 == hash(collision_2)

        hi = self.hi
        hi.consume(GG)
        hi.consume(collision_1)

        assert hi.get(GG) == 1
        assert hi.get(GGhash) == 1

    def test_collision_2(self):

        GG = 'G' * 12                   # forward_hash: 11184810
        assert khmer.forward_hash(GG, 12) == 11184810

        collision_1 = 'AAACGTATGACT'
        assert khmer.forward_hash(collision_1, 12) == 184777

        collision_2 = 'AAATACCGAGCG'
        assert khmer.forward_hash(collision_2, 12) == 76603

        # hash(GG) % 1000003 == hash(collision_1)
        # hash(GG) % 1009837 == hash(collision_2)

        hi = self.hi
        hi.consume(GG)
        hi.consume(collision_2)

        assert hi.get(GG) == 1

    def test_collision_3(self):

        GG = 'G' * 12                   # forward_hash: 11184810
        assert khmer.forward_hash(GG, 12) == 11184810

        collision_1 = 'AAACGTATGACT'
        assert khmer.forward_hash(collision_1, 12) == 184777

        collision_2 = 'AAATACCGAGCG'
        assert khmer.forward_hash(collision_2, 12) == 76603

        # hash(GG) % 1000003 == hash(collision_1)
        # hash(GG) % 1009837 == hash(collision_2)

        hi = self.hi
        hi.consume(GG)
        hi.consume(collision_1)
        hi.consume(collision_2)

        assert hi.get(GG) == 2


def test_get_raw_tables():
    ht = khmer.Countgraph(20, 1e5, 4)
    tables = ht.get_raw_tables()

    for size, table in zip(ht.hashsizes(), tables):
        assert isinstance(table, memoryview)
        assert size == len(table)


def test_get_raw_tables_view():
    ht = khmer.Countgraph(20, 1e5, 4)
    tables = ht.get_raw_tables()
    for tab in tables:
        assert sum(tab.tolist()) == 0
    ht.consume('AAAATTTTCCCCGGGGAAAA')
    for tab in tables:
        assert sum(tab.tolist()) == 1


@attr('huge')
def test_toobig():
    try:
        ct = khmer.Countgraph(30, 1e13, 1)
        assert 0, "this should fail"
    except MemoryError as err:
        print(str(err))


def test_3_tables():
    x = list(PRIMES_1m)
    x.append(1000005)

    hi = khmer._Countgraph(12, x)

    GG = 'G' * 12                   # forward_hash: 11184810
    assert khmer.forward_hash(GG, 12) == 11184810

    collision_1 = 'AAACGTATGACT'
    assert khmer.forward_hash(collision_1, 12) == 184777

    collision_2 = 'AAATACCGAGCG'
    assert khmer.forward_hash(collision_2, 12) == 76603

    collision_3 = 'AAACGTATCGAG'
    assert khmer.forward_hash(collision_3, 12) == 184755

    # hash(GG) % 1000003 == hash(collision_1)
    # hash(GG) % 1009837 == hash(collision_2)
    # hash(GG) % 1000005 == hash(collision_3)
    hi.consume(GG)
    assert hi.get(GG) == 1

    hi.consume(collision_1)
    assert hi.get(GG) == 1

    hi.consume(collision_2)
    assert hi.get(GG) == 1

    hi.consume(collision_3)
    assert hi.get(GG) == 2


def test_simple_median():
    hi = khmer.Countgraph(6, 1e6, 2)

    hi.consume("AAAAAA")
    (median, average, stddev) = hi.get_median_count("AAAAAA")
    print(median, average, stddev)
    assert median == 1
    assert average == 1.0
    assert stddev == 0.0

    hi.consume("AAAAAA")
    (median, average, stddev) = hi.get_median_count("AAAAAA")
    print(median, average, stddev)
    assert median == 2
    assert average == 2.0
    assert stddev == 0.0

    hi.consume("AAAAAT")
    (median, average, stddev) = hi.get_median_count("AAAAAAT")
    print(median, average, stddev)
    assert median == 2
    assert average == 1.5
    assert int(stddev * 100) == 50        # .5

    hi.consume("AAAAAT")
    (median, average, stddev) = hi.get_median_count("AAAAAAT")
    print(median, average, stddev)
    assert median == 2
    assert average == 2.0
    assert stddev == 0.0

    hi.consume("AAAAAT")
    (median, average, stddev) = hi.get_median_count("AAAAAAT")
    print(median, average, stddev)
    assert median == 3
    assert average == 2.5
    assert int(stddev * 100) == 50        # .5


def test_median_too_short():
    hi = khmer.Countgraph(6, 1e6, 2)

    hi.consume("AAAAAA")
    try:
        hi.get_median_count("A")
        assert 0, "this should fail"
    except ValueError:
        pass


def test_median_at_least():
    hi = khmer.Countgraph(6, 1e6, 2)

    hi.consume("AAAAAA")
    assert hi.median_at_least("AAAAAA", 1)
    assert hi.median_at_least("AAAAAA", 2) is False

    hi.consume("AAAAAA")
    assert hi.median_at_least("AAAAAA", 2)
    assert hi.median_at_least("AAAAAA", 3) is False

    hi.consume("AAAAAA")
    assert hi.median_at_least("AAAAAA", 3)
    assert hi.median_at_least("AAAAAA", 4) is False

    hi.consume("AAAAAA")
    assert hi.median_at_least("AAAAAA", 4)
    assert hi.median_at_least("AAAAAA", 5) is False

    hi.consume("AAAAAA")
    assert hi.median_at_least("AAAAAA", 5)
    assert hi.median_at_least("AAAAAA", 6) is False


def test_median_at_least_single_gt():
    K = 20
    hi = khmer.Countgraph(K, 1e6, 2)

    kmers = ['ATCGATCGATCGATCGATCG',
             'GTACGTACGTACGTACGTAC',
             'TTAGTTAGTTAGTTAGTTAG']

    for kmer in kmers:
        hi.consume(kmer)
        assert hi.median_at_least(kmer, 1) is True


def test_median_at_least_single_lt():
    K = 20
    hi = khmer.Countgraph(K, 1e6, 2)

    kmers = ['ATCGATCGATCGATCGATCG',
             'GTACGTACGTACGTACGTAC',
             'TTAGTTAGTTAGTTAGTTAG']

    for kmer in kmers:
        hi.consume(kmer)
        assert hi.median_at_least(kmer, 2) is False


def test_median_at_least_odd_gt():
    # test w/odd number of k-mers
    K = 20
    hi = khmer.Countgraph(K, 1e6, 2)

    seqs = ['ATCGATCGATCGATCGATCGCC',
            'GTACGTACGTACGTACGTACCC',
            'TTAGTTAGTTAGTTAGTTAGCC']

    for seq in seqs:
        hi.consume(seq)
        assert hi.median_at_least(seq, 1) is True


def test_median_at_least_odd_lt():
    K = 20
    hi = khmer.Countgraph(K, 1e6, 2)

    seqs = ['ATCGATCGATCGATCGATCGCC',
            'GTACGTACGTACGTACGTACCC',
            'TTAGTTAGTTAGTTAGTTAGCC']

    for seq in seqs:
        hi.consume(seq)
        assert hi.median_at_least(seq, 2) is False


# Test median with even number of k-mers
def test_median_at_least_even_gt():
    K = 20
    hi = khmer.Countgraph(K, 1e6, 2)

    seqs = ['ATCGATCGATCGATCGATCGCCC',
            'GTACGTACGTACGTACGTACCCC',
            'TTAGTTAGTTAGTTAGTTAGCCC']

    for seq in seqs:
        hi.consume(seq)
        assert hi.median_at_least(seq, 1) is True


def test_median_at_least_even_lt():
    K = 20
    hi = khmer.Countgraph(K, 1e6, 2)

    seqs = ['ATCGATCGATCGATCGATCGCCC',
            'GTACGTACGTACGTACGTACCCC',
            'TTAGTTAGTTAGTTAGTTAGCCC']

    for seq in seqs:
        hi.consume(seq)
        assert hi.median_at_least(seq, 2) is False


def test_median_at_least_comp():
    K = 20
    C = 4
    hi = khmer.Countgraph(K, 1e6, 2)

    seqs = ['ATCGATCGATCGATCGATCGCCC',
            'GTACGTACGTACGTACGTACCCC',
            'TTAGTTAGTTAGTTAGTTAGCCC']

    for seq in seqs:
        hi.consume(seq)
        hi.consume(seq)
        hi.consume(seq)

        med, _, _ = hi.get_median_count(seq)
        assert hi.median_at_least(seq, C) is (med >= C)


def test_median_at_least_exception():
    ht = khmer.Countgraph(20, 1e6, 2)
    try:
        ht.median_at_least('ATGGCTGATCGAT', 1)
        assert 0, "should have thrown ValueError"
    except ValueError as e:
        pass


def test_get_kmer_counts_too_short():
    hi = khmer.Countgraph(6, 1e6, 2)

    hi.consume("AAAAAA")
    counts = hi.get_kmer_counts("A")
    assert len(counts) == 0


def test_get_kmer_hashes_too_short():
    hi = khmer.Countgraph(6, 1e6, 2)

    hi.consume("AAAAAA")
    hashes = hi.get_kmer_hashes("A")
    assert len(hashes) == 0


def test_get_kmers_too_short():
    hi = khmer.Countgraph(6, 1e6, 2)

    hi.consume("AAAAAA")
    kmers = hi.get_kmers("A")
    assert len(kmers) == 0


def test_get_kmer_counts():
    hi = khmer.Countgraph(6, 1e6, 2)

    hi.consume("AAAAAA")
    counts = hi.get_kmer_counts("AAAAAA")
    print(counts)
    assert len(counts) == 1
    assert counts[0] == 1

    hi.consume("AAAAAA")
    counts = hi.get_kmer_counts("AAAAAA")
    print(counts)
    assert len(counts) == 1
    assert counts[0] == 2

    hi.consume("AAAAAT")
    counts = hi.get_kmer_counts("AAAAAAT")
    print(counts)
    assert len(counts) == 2
    assert counts[0] == 2
    assert counts[1] == 1

    hi.consume("AAAAAT")
    counts = hi.get_kmer_counts("AAAAAAT")
    print(counts)
    assert len(counts) == 2
    assert counts[0] == 2
    assert counts[1] == 2

    hi.consume("AAAAAT")
    counts = hi.get_kmer_counts("AAAAAAT")
    print(counts)
    assert len(counts) == 2
    assert counts[0] == 2
    assert counts[1] == 3


def test_get_kmer_hashes():
    hi = khmer.Countgraph(6, 1e6, 2)

    hi.consume("AAAAAA")
    hashes = hi.get_kmer_hashes("AAAAAA")
    print(hashes)
    assert len(hashes) == 1
    assert hi.get(hashes[0]) == 1

    hi.consume("AAAAAA")
    hashes = hi.get_kmer_hashes("AAAAAA")
    print(hashes)
    assert len(hashes) == 1
    assert hi.get(hashes[0]) == 2

    hi.consume("AAAAAT")
    hashes = hi.get_kmer_hashes("AAAAAAT")
    print(hashes)
    assert len(hashes) == 2
    assert hi.get(hashes[0]) == 2
    assert hi.get(hashes[1]) == 1

    hi.consume("AAAAAT")
    hashes = hi.get_kmer_hashes("AAAAAAT")
    print(hashes)
    assert len(hashes) == 2
    assert hi.get(hashes[0]) == 2
    assert hi.get(hashes[1]) == 2

    hi.consume("AAAAAT")
    hashes = hi.get_kmer_hashes("AAAAAAT")
    print(hashes)
    assert len(hashes) == 2
    assert hi.get(hashes[0]) == 2
    assert hi.get(hashes[1]) == 3


def test_get_kmers():
    hi = khmer.Countgraph(6, 1e6, 2)

    kmers = hi.get_kmers("AAAAAA")
    assert kmers == ["AAAAAA"]

    kmers = hi.get_kmers("AAAAAAT")
    assert kmers == ["AAAAAA", "AAAAAT"]


@attr("huge")
def test_save_load_large():
    def do_test(ctfile):
        inpath = utils.get_test_data('random-20-a.fa')
        savepath = utils.get_temp_filename(ctfile)

        sizes = khmer.get_n_primes_near_x(1, 2 ** 31 + 1000)

        orig = khmer._Countgraph(12, sizes)
        orig.consume_fasta(inpath)
        orig.save(savepath)

        loaded = khmer.load_countgraph(savepath)

        orig_count = orig.n_occupied()
        loaded_count = loaded.n_occupied()
        assert orig_count == 3966, orig_count
        assert loaded_count == orig_count, loaded_count

    for ctfile in ['temp.ct.gz', 'temp.ct']:
        do_test(ctfile)


def test_save_load_occupied():
    def do_test(ctfile):
        print('working with', ctfile)
        inpath = utils.get_test_data('random-20-a.fa')
        savepath = utils.get_temp_filename(ctfile)

        orig = khmer.Countgraph(12, 1e5, 4)
        orig.consume_fasta(inpath)
        orig.save(savepath)

        loaded = khmer.load_countgraph(savepath)

        orig_count = orig.n_occupied()
        loaded_count = loaded.n_occupied()
        assert orig_count == 3886, orig_count
        assert loaded_count == orig_count, loaded_count

    for ctfile in ['temp.ct', 'temp.ct.gz']:
        do_test(ctfile)


def test_save_load():
    inpath = utils.get_test_data('random-20-a.fa')
    savepath = utils.get_temp_filename('tempcountingsave0.ht')

    sizes = list(PRIMES_1m)
    sizes.append(1000005)

    hi = khmer._Countgraph(12, sizes)
    hi.consume_fasta(inpath)
    hi.save(savepath)

    ht = khmer._Countgraph(12, sizes)
    try:
        ht.load(savepath)
    except OSError as err:
        assert 0, 'Should not produce an OSError: ' + str(err)

    tracking = khmer._Nodegraph(12, sizes)
    x = hi.abundance_distribution(inpath, tracking)

    tracking = khmer._Nodegraph(12, sizes)
    y = ht.abundance_distribution(inpath, tracking)

    assert sum(x) == 3966, sum(x)
    assert x == y, (x, y)


def test_load_truncated():
    inpath = utils.get_test_data('random-20-a.fa')
    savepath = utils.get_temp_filename('save.ht')
    truncpath = utils.get_temp_filename('trunc.ht')

    sizes = khmer.get_n_primes_near_x(3, 200)

    hi = khmer._Countgraph(12, sizes)
    hi.consume_fasta(inpath)
    hi.save(savepath)

    data = open(savepath, 'rb').read()
    for i in range(len(data)):
        fp = open(truncpath, 'wb')
        fp.write(data[:i])
        fp.close()

        try:
            ht = khmer.load_countgraph(truncpath)
            assert 0, "this should not be reached!"
        except OSError as err:
            print(str(err))


def test_load_gz():
    inpath = utils.get_test_data('random-20-a.fa')

    savepath = utils.get_temp_filename('tempcountingsave1.ht')
    loadpath = utils.get_temp_filename('tempcountingsave1.ht.gz')

    sizes = list(PRIMES_1m)
    sizes.append(1000005)

    # save uncompressed hashtable.
    hi = khmer._Countgraph(12, sizes)
    hi.consume_fasta(inpath)
    hi.save(savepath)

    # compress.
    in_file = open(savepath, 'rb')
    out_file = gzip.open(loadpath, 'wb')
    out_file.writelines(in_file)
    out_file.close()
    in_file.close()

    # load compressed hashtable.
    ht = khmer._Countgraph(12, sizes)
    try:
        ht.load(loadpath)
    except OSError as err:
        assert 0, "Should not produce an OSError: " + str(err)

    tracking = khmer._Nodegraph(12, sizes)
    x = hi.abundance_distribution(inpath, tracking)

    tracking = khmer._Nodegraph(12, sizes)
    y = ht.abundance_distribution(inpath, tracking)

    assert sum(x) == 3966, sum(x)
    assert x == y, (x, y)


def test_save_load_gz():
    inpath = utils.get_test_data('random-20-a.fa')
    savepath = utils.get_temp_filename('tempcountingsave2.ht.gz')

    sizes = list(PRIMES_1m)
    sizes.append(1000005)

    hi = khmer._Countgraph(12, sizes)
    hi.consume_fasta(inpath)
    hi.save(savepath)

    ht = khmer._Countgraph(12, sizes)
    try:
        ht.load(savepath)
    except OSError as err:
        assert 0, 'Should not produce an OSError: ' + str(err)

    tracking = khmer._Nodegraph(12, sizes)
    x = hi.abundance_distribution(inpath, tracking)

    tracking = khmer._Nodegraph(12, sizes)
    y = ht.abundance_distribution(inpath, tracking)

    assert sum(x) == 3966, sum(x)
    assert x == y, (x, y)


def test_load_empty_files():
    def do_load_ct(fname):
        with assert_raises(OSError):
            ct = khmer.load_countgraph(fname)

    # Check empty files, compressed or not
    for ext in ['', '.gz']:
        fn = utils.get_test_data('empty-file' + ext)
        do_load_ct(fn)


def test_trim_full():
    hi = khmer.Countgraph(6, 1e6, 2)

    hi.consume(DNA)
    hi.consume(DNA)

    seq, pos = hi.trim_on_abundance(DNA, 2)
    assert DNA == seq, seq


def test_trim_short():
    hi = khmer.Countgraph(6, 1e6, 2)

    hi.consume(DNA)
    hi.consume(DNA[:50])

    seq, pos = hi.trim_on_abundance(DNA, 2)
    assert DNA[:50] == seq, (seq, pos)
    assert hi.get(seq[-6:]) == 2
    assert hi.get(DNA[:51][-6:]) == 1


def test_find_spectral_error_positions_1():
    hi = khmer.Countgraph(8, 1e6, 2)

    hi.consume(DNA)
    hi.consume(DNA[:30])

    for n in range(len(DNA) - 8 + 1):
        print(n, hi.get(DNA[n:n + 8]))

    posns = hi.find_spectral_error_positions(DNA, 1)
    assert posns == [30], posns


def test_find_spectral_error_positions_2():
    hi = khmer.Countgraph(8, 1e6, 2)

    hi.consume(DNA)
    hi.consume(DNA)

    posns = hi.find_spectral_error_positions(DNA, 2)
    assert posns == [], posns


def test_find_spectral_error_positions_6():
    hi = khmer.Countgraph(8, 1e6, 2)

    hi.consume(DNA)
    hi.consume(DNA[1:])

    for n in range(len(DNA) - 8 + 1):
        print(n, hi.get(DNA[n:n + 8]))

    posns = hi.find_spectral_error_positions(DNA, 1)
    assert posns == [0], posns


def test_find_spectral_error_positions_4():
    hi = khmer.Countgraph(8, 1e6, 2)

    hi.consume(DNA)

    posns = hi.find_spectral_error_positions(DNA, 2)
    assert posns == [], posns


def test_find_spectral_error_positions_5():
    hi = khmer.Countgraph(8, 1e6, 2)

    hi.consume(DNA)
    hi.consume(DNA[:10])
    hi.consume(DNA[11:])

    posns = hi.find_spectral_error_positions(DNA, 1)
    assert posns == [10], posns


def test_find_spectral_error_locs7():
    K = 8
    hi = khmer.Countgraph(K, 1e6, 2)

    hi.consume(DNA)
    hi.consume(DNA[K:])

    for n in range(len(DNA) - 8 + 1):
        print(n, hi.get(DNA[n:n + 8]))

    posns = hi.find_spectral_error_positions(DNA, 1)
    assert posns == [7], posns


def test_find_spectral_error_positions_err():
    hi = khmer.Countgraph(8, 1e6, 2)

    try:
        posns = hi.find_spectral_error_positions(DNA[:6], 1)
        assert 0, "should raise ValueError; too short"
    except ValueError:
        pass

    try:
        posns = hi.find_spectral_error_positions("ACGTACGN", 1)
        assert 0, "should raise ValueError; contains N"
    except ValueError:
        pass


def test_maxcount():
    # hashtable should saturate at some point so as not to overflow counter
    kh = khmer.Countgraph(4, 4 ** 4, 4)
    kh.set_use_bigcount(False)

    last_count = None
    for i in range(0, 1000):
        kh.count('AAAA')
        c = kh.get('AAAA')

        if c == last_count:
            break
        last_count = c

    assert c != 1000, "should not be able to count to 1000: %d" % c
    assert c == MAX_COUNT, c       # this will depend on HashcountType...


def test_maxcount_with_bigcount():
    # hashtable should not saturate, if use_bigcount is set.
    kh = khmer.Countgraph(4, 4 ** 4, 4)
    kh.set_use_bigcount(True)

    last_count = None
    for i in range(0, 1000):
        kh.count('AAAA')
        c = kh.get('AAAA')

        if c == last_count:
            break
        last_count = c

    assert c == 1000, "should be able to count to 1000: %d" % c
    assert c != MAX_COUNT, c


def test_maxcount_with_bigcount_save():
    # hashtable should not saturate, if use_bigcount is set.
    kh = khmer.Countgraph(4, 4 ** 4, 4)
    kh.set_use_bigcount(True)

    for i in range(0, 1000):
        kh.count('AAAA')
        c = kh.get('AAAA')

    savepath = utils.get_temp_filename('tempcountingsave.ht')
    kh.save(savepath)

    kh = khmer.Countgraph(1, 1, 1)
    try:
        kh.load(savepath)
    except OSError as err:
        assert 0, "Should not produce an OSError: " + str(err)

    c = kh.get('AAAA')
    assert c == 1000, "should be able to count to 1000: %d" % c
    assert c != MAX_COUNT, c


def test_bigcount_save():
    # hashtable should not saturate, if use_bigcount is set.
    kh = khmer.Countgraph(4, 4 ** 4, 4)
    kh.set_use_bigcount(True)

    savepath = utils.get_temp_filename('tempcountingsave.ht')
    kh.save(savepath)

    kh = khmer.Countgraph(1, 1, 1)
    try:
        kh.load(savepath)
    except OSError as err:
        assert 0, "Should not produce an OSError: " + str(err)

    # set_use_bigcount should still be True after load (i.e. should be saved)

    assert kh.get('AAAA') == 0

    for i in range(0, 1000):
        kh.count('AAAA')
        kh.get('AAAA')

    assert kh.get('AAAA') == 1000


def test_nobigcount_save():
    kh = khmer.Countgraph(4, 4 ** 4, 4)
    # kh.set_use_bigcount(False) <-- this is the default

    savepath = utils.get_temp_filename('tempcountingsave.ht')
    kh.save(savepath)

    kh = khmer.Countgraph(1, 1, 1)
    try:
        kh.load(savepath)
    except OSError as err:
        assert 0, 'Should not produce an OSError: ' + str(err)

    # set_use_bigcount should still be False after load (i.e. should be saved)

    assert kh.get('AAAA') == 0

    for i in range(0, 1000):
        kh.count('AAAA')
        kh.get('AAAA')

    assert kh.get('AAAA') == MAX_COUNT


def test_bigcount_abund_dist():
    kh = khmer.Countgraph(18, 1e2, 4)
    tracking = khmer.Nodegraph(18, 1e2, 4)
    kh.set_use_bigcount(True)

    seqpath = utils.get_test_data('test-abund-read-2.fa')

    kh.consume_fasta(seqpath)

    dist = kh.abundance_distribution(seqpath, tracking)
    print(kh.get('GGTTGACGGGGCTCAGGG'))

    pdist = [(i, dist[i]) for i in range(len(dist)) if dist[i]]
    assert dist[1002] == 1, pdist


def test_bigcount_abund_dist_2():
    kh = khmer.Countgraph(18, 1e7, 4)
    tracking = khmer.Nodegraph(18, 1e7, 4)
    kh.set_use_bigcount(True)

    seqpath = utils.get_test_data('test-abund-read.fa')

    kh.consume_fasta(seqpath)
    for i in range(1000):
        kh.count('GGTTGACGGGGCTCAGGG')

    dist = kh.abundance_distribution(seqpath, tracking)
    print(kh.get('GGTTGACGGGGCTCAGGG'))

    pdist = [(i, dist[i]) for i in range(len(dist)) if dist[i]]
    assert dist[1001] == 1, pdist


def test_bigcount_overflow():
    kh = khmer.Countgraph(18, 1e7, 4)
    kh.set_use_bigcount(True)

    for i in range(0, 70000):
        kh.count('GGTTGACGGGGCTCAGGG')

    assert kh.get('GGTTGACGGGGCTCAGGG') == MAX_BIGCOUNT


def test_get_ksize():
    kh = khmer.Countgraph(22, 1, 1)
    assert kh.ksize() == 22


def test_get_hashsizes():
    kh = khmer.Countgraph(22, 100, 4)
    # Py2/3 hack, longify converts to long in py2, remove once py2 isn't
    # supported any longer.
    expected = utils.longify([97, 89, 83, 79])
    assert kh.hashsizes() == expected, kh.hashsizes()


# def test_collect_high_abundance_kmers():
#    seqpath = utils.get_test_data('test-abund-read-2.fa')
#
#    kh = khmer.Countgraph(18, 1e6, 4)
#    hb = kh.collect_high_abundance_kmers(seqpath, 2, 4)


def test_load_notexist_should_fail():
    savepath = utils.get_temp_filename('tempcountingsave0.ht')

    hi = khmer.Countgraph(12, 1000, 2)
    try:
        hi.load(savepath)
        assert 0, "load should fail"
    except OSError as e:
        print(str(e))


def test_load_truncated_should_fail():
    inpath = utils.get_test_data('random-20-a.fa')
    savepath = utils.get_temp_filename('tempcountingsave0.ht')

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


def test_load_gz_notexist_should_fail():
    savepath = utils.get_temp_filename('tempcountingsave0.ht.gz')

    hi = khmer.Countgraph(12, 1000, 2)
    try:
        hi.load(savepath)
        assert 0, "load should fail"
    except OSError as e:
        print(str(e))


def test_load_gz_truncated_should_fail():
    inpath = utils.get_test_data('random-20-a.fa')
    savepath = utils.get_temp_filename('tempcountingsave0.ht.gz')

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


def test_counting_file_version_check():
    ht = khmer.Countgraph(12, 1, 1)

    inpath = utils.get_test_data('badversion-k12.ct')

    try:
        ht.load(inpath)
        assert 0, "this should fail"
    except OSError as e:
        print(str(e))


def test_counting_gz_file_version_check():
    ht = khmer.Countgraph(12, 1, 1)

    inpath = utils.get_test_data('badversion-k12.ct.gz')

    try:
        ht.load(inpath)
        assert 0, "this should fail"
    except OSError as e:
        print(str(e))


def test_counting_file_type_check():
    inpath = utils.get_test_data('goodversion-k12.ht')

    kh = khmer.Countgraph(12, 1, 1)

    try:
        kh.load(inpath)
        assert 0, "this should fail"
    except OSError as e:
        print(str(e))


def test_counting_gz_file_type_check():
    ht = khmer.Nodegraph(12, 1, 1)

    inpath = utils.get_test_data('goodversion-k12.ht.gz')

    kh = khmer.Countgraph(12, 1, 1)

    try:
        kh.load(inpath)
        assert 0, "this should fail"
    except OSError as e:
        print(str(e))


def test_counting_bad_primes_list():
    try:
        ht = khmer._Countgraph(12, ["a", "b", "c"], 1)
        assert 0, "bad list of primes should fail"
    except TypeError as e:
        print(str(e))


def test_bad_use_bigcount():
    countgraph = khmer.Countgraph(4, 4 ** 4, 4)
    countgraph.set_use_bigcount(True)
    assert countgraph.get_use_bigcount()
    try:
        countgraph.get_use_bigcount(True)
        assert 0, "this should fail"
    except TypeError as err:
        print(str(err))


def test_consume_absentfasta():
    countgraph = khmer.Countgraph(4, 4 ** 4, 4)
    try:
        countgraph.consume_fasta("absent_file.fa")
        assert 0, "This should fail"
    except OSError as err:
        print(str(err))


def test_consume_absentfasta_with_reads_parser():
    countgraph = khmer.Countgraph(4, 4 ** 4, 4)
    try:
        countgraph.consume_fasta_with_reads_parser()
        assert 0, "this should fail"
    except TypeError as err:
        print(str(err))
    try:
        readparser = ReadParser(utils.get_test_data('empty-file'))
        countgraph.consume_fasta_with_reads_parser(readparser)
        assert 0, "this should fail"
    except OSError as err:
        print(str(err))
    except ValueError as err:
        print(str(err))


def test_badconsume():
    countgraph = khmer.Countgraph(4, 4 ** 4, 4)
    try:
        countgraph.consume()
        assert 0, "this should fail"
    except TypeError as err:
        print(str(err))
    try:
        countgraph.consume("AAA")
        assert 0, "this should fail"
    except ValueError as err:
        print(str(err))


def test_get_badmin_count():
    countgraph = khmer.Countgraph(4, 4 ** 4, 4)
    try:
        countgraph.get_min_count()
        assert 0, "this should fail"
    except TypeError as err:
        print(str(err))
    try:
        countgraph.get_min_count("AAA")
        assert 0, "this should fail"
    except ValueError as err:
        print(str(err))


def test_get_badmax_count():
    countgraph = khmer.Countgraph(4, 4 ** 4, 4)
    try:
        countgraph.get_max_count()
        assert 0, "this should fail"
    except TypeError as err:
        print(str(err))
    try:
        countgraph.get_max_count("AAA")
        assert 0, "this should fail"
    except ValueError as err:
        print(str(err))


def test_get_badmedian_count():
    countgraph = khmer.Countgraph(4, 4 ** 4, 4)
    try:
        countgraph.get_median_count()
        assert 0, "this should fail"
    except TypeError as err:
        print(str(err))
    try:
        countgraph.get_median_count("AAA")
        assert 0, "this should fail"
    except ValueError as err:
        print(str(err))


def test_badget():
    countgraph = khmer.Countgraph(4, 4 ** 4, 4)
    try:
        countgraph.get()
        assert 0, "this should fail"
    except TypeError as err:
        print(str(err))


def test_badget_2():
    countgraph = khmer.Countgraph(6, 1e6, 2)

    countgraph.consume(DNA)

    assert countgraph.get("AGCTTT") == 1

    assert countgraph.get("GATGAG") == 0

    try:
        countgraph.get("AGCTT")
        assert 0, "this should fail"
    except ValueError as err:
        print(str(err))


def test_badtrim():
    countgraph = khmer.Countgraph(6, 1e6, 2)

    countgraph.consume(DNA)
    try:
        countgraph.trim_on_abundance()
        assert 0, "this should fail"
    except TypeError as err:
        print(str(err))
    countgraph.trim_on_abundance("AAAAAA", 1)


def test_badfasta_count_kmers_by_position():
    countgraph = khmer.Countgraph(4, 4 ** 4, 4)
    try:
        countgraph.fasta_count_kmers_by_position()
    except TypeError as err:
        print(str(err))

    filename = utils.get_test_data("test-short.fa")
    try:
        countgraph.fasta_count_kmers_by_position(filename, -1, 0)
        assert 0, "this should fail"
    except ValueError as err:
        print(str(err))
    try:
        countgraph.fasta_count_kmers_by_position(filename, 0, -1)
        assert 0, "this should fail"
    except ValueError as err:
        print(str(err))


def test_badload():
    countgraph = khmer.Countgraph(4, 4 ** 4, 4)
    try:
        countgraph.load()
        assert 0, "this should fail"
    except TypeError as err:
        print(str(err))


def test_badsave():
    countgraph = khmer.Countgraph(4, 4 ** 4, 4)
    try:
        countgraph.save()
        assert 0, "this should fail"
    except TypeError as err:
        print(str(err))


def test_badksize():
    countgraph = khmer.Countgraph(4, 4 ** 4, 4)
    try:
        countgraph.ksize(True)
        assert 0, "this should fail"
    except TypeError as err:
        print(str(err))


def test_badhashsizes():
    countgraph = khmer.Countgraph(4, 4 ** 4, 4)
    try:
        countgraph.hashsizes(True)
        assert 0, "this should fail"
    except TypeError as err:
        print(str(err))


def test_badconsume_and_tag():
    countgraph = khmer.Countgraph(4, 4 ** 4, 4)
    try:
        countgraph.consume_and_tag()
        assert 0, "this should fail"
    except TypeError as err:
        print(str(err))


def test_consume_fasta_and_tag():
    countgraph = khmer.Countgraph(4, 4 ** 4, 4)
    try:
        countgraph.consume_fasta_and_tag()
        assert 0, "this should fail"
    except TypeError as err:
        print(str(err))
    countgraph.consume_fasta_and_tag(utils.get_test_data("test-graph2.fa"))


def test_consume_and_retrieve_tags_1():
    ct = khmer.Countgraph(4, 4 ** 4, 4)

    # first, for each sequence, build tags.
    for record in screed.open(utils.get_test_data('test-graph2.fa')):
        ct.consume_and_tag(record.sequence)

    # check that all the tags in sequences are retrieved by iterating
    # across the sequence and retrieving by neighborhood.

    ss = set()
    tt = set()
    for record in screed.open(utils.get_test_data('test-graph2.fa')):
        for p, tag in ct.get_tags_and_positions(record.sequence):
            ss.add(tag)

        for start in range(len(record.sequence) - 3):
            kmer = record.sequence[start:start + 4]
            tt.update(ct.find_all_tags_list(kmer))

    assert ss == tt


def test_consume_and_retrieve_tags_empty():
    ct = khmer.Countgraph(4, 4 ** 4, 4)

    # load each sequence but do not build tags - everything should be empty.
    for record in screed.open(utils.get_test_data('test-graph2.fa')):
        ct.consume(record.sequence)

    # check that all the tags in sequences are retrieved by iterating
    # across the sequence and retrieving by neighborhood.

    ss = set()
    tt = set()
    for record in screed.open(utils.get_test_data('test-graph2.fa')):
        for p, tag in ct.get_tags_and_positions(record.sequence):
            ss.add(tag)

        for start in range(len(record.sequence) - 3):
            kmer = record.sequence[start:start + 4]
            tt.update(ct.find_all_tags_list(kmer))

    assert not ss
    assert not tt


def test_find_all_tags_list_error():
    ct = khmer.Countgraph(4, 4 ** 4, 4)

    # load each sequence but do not build tags - everything should be empty.
    for record in screed.open(utils.get_test_data('test-graph2.fa')):
        ct.consume(record.sequence)

    try:
        ct.find_all_tags_list("ATA")
        assert False, "a ValueError should be raised for incorrect k-mer size"
    except ValueError:
        pass

    try:
        ct.find_all_tags_list("ATAGA")
        assert False, "a ValueError should be raised for incorrect k-mer size"
    except ValueError:
        pass


def test_abund_dist_gz_bigcount():
    infile = utils.get_temp_filename('test.fa')
    shutil.copyfile(utils.get_test_data('test-abund-read-2.fa'), infile)
    script = 'load-into-counting.py'
    htfile = utils.get_temp_filename('test_ct')
    args = ['-x', str(1e7), '-N', str(2), '-k', str(2), htfile, infile]
    utils.runscript(script, args)  # create a bigcount table
    assert os.path.exists(htfile)
    data = open(htfile, 'rb').read()

    outfile = utils.get_temp_filename('test_ct.gz')
    f_out = gzip.open(outfile, 'wb')  # compress the created bigcount table
    f_out.write(data)
    f_out.close()
    # load the compressed bigcount table
    try:
        countgraph = khmer.load_countgraph(outfile)
    except OSError as err:
        assert 0, 'Should not produce OSError: ' + str(err)

    assert countgraph.n_occupied() != 0
    hashsizes = countgraph.hashsizes()
    kmer_size = countgraph.ksize()
    tracking = khmer._Nodegraph(kmer_size, hashsizes)
    abundances = countgraph.abundance_distribution(infile, tracking)
    # calculate abundance distribution for compressed bigcount table
    flag = False
    # check if abundance is > 255
    # if ok  gzipped bigcount was loaded correctly
    for _, i in enumerate(abundances):
        print(_, i)
        if _ > 255 and i > 0:
            flag = True
            break
    assert flag


def test_abund_dist_gz_bigcount_compressed_first():
    infile = utils.get_temp_filename('test.fa')
    shutil.copyfile(utils.get_test_data('test-abund-read-2.fa'), infile)
    script = 'load-into-counting.py'
    htfile = utils.get_temp_filename('test_ct.gz')
    args = ['-x', str(1e7), '-N', str(2), '-k', str(2), htfile, infile]
    utils.runscript(script, args)  # create a bigcount table
    assert os.path.exists(htfile)
    data = gzip.open(htfile, 'rb').read()  # read compressed bigcount table

    outfile = utils.get_temp_filename('test_ct')
    f_out = open(outfile, 'wb')  # output the bigcount table
    f_out.write(data)
    f_out.close()
    # load the compressed bigcount table
    try:
        countgraph = khmer.load_countgraph(outfile)
    except OSError as err:
        assert 0, 'Should not produce OSError: ' + str(err)

    assert countgraph.n_occupied() != 0
    hashsizes = countgraph.hashsizes()
    kmer_size = countgraph.ksize()
    tracking = khmer._Nodegraph(kmer_size, hashsizes)
    abundances = countgraph.abundance_distribution(infile, tracking)
    # calculate abundance distribution for compressed bigcount table
    flag = False
    # check if abundance is > 255
    # if ok  gzipped bigcount was loaded correctly
    for _, i in enumerate(abundances):
        print(_, i)
        if _ > 255 and i > 0:
            flag = True
            break
    assert flag


def test_counting_load_bigcount():
    count_table = khmer.Countgraph(10, 1e5, 4)
    count_table.set_use_bigcount(True)
    for i in range(500):
        print(i, count_table.count('ATATATATAT'))
    count = count_table.get('ATATATATAT')
    assert count == 500
