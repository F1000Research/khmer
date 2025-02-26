#! /usr/bin/env python
#
# This file is part of khmer, http://github.com/ged-lab/khmer/, and is
# Copyright (C) Michigan State University, 2009-2015. It is licensed under
# the three-clause BSD license; see doc/LICENSE.txt.
# Contact: khmer-project@idyll.org
#
# pylint: disable=missing-docstring
"""
Build a graph from the given sequences, save in <ptname>.

% python scripts/load-graph.py <ptname> <data1> [ <data2> <...> ]

Use '-h' for parameter help.
"""

from __future__ import print_function, absolute_import, unicode_literals

import sys

import khmer
from khmer import khmer_args
from khmer.khmer_args import (report_on_config, info, add_threading_args,
                              calculate_graphsize)
from khmer.kfile import check_input_files, check_space
from khmer.kfile import check_space_for_graph
from oxli import functions as oxfuncs


def build_parser(parser):
    add_threading_args(parser)
    parser.add_argument('--no-build-tagset', '-n', default=False,
                        action='store_true', dest='no_build_tagset',
                        help='Do NOT construct tagset while loading sequences')
    parser.add_argument('output_filename',
                        metavar='output_nodegraph_filename', help='output'
                        ' k-mer nodegraph filename.')
    parser.add_argument('input_filenames', metavar='input_sequence_filename',
                        nargs='+', help='input FAST[AQ] sequence filename')
    parser.add_argument('-f', '--force', default=False, action='store_true',
                        help='Overwrite output file if it exists')
    return parser


def main(args):
    info('build-graph.py', ['graph', 'SeqAn'])

    report_on_config(args, graphtype='nodegraph')
    base = args.output_filename
    filenames = args.input_filenames

    for fname in args.input_filenames:
        check_input_files(fname, args.force)

    graphsize = calculate_graphsize(args, 'nodegraph')
    check_space_for_graph(args.output_filename, graphsize, args.force)

    print('Saving k-mer nodegraph to %s' % base, file=sys.stderr)
    print('Loading kmers from sequences in %s' %
          repr(filenames), file=sys.stderr)
    if args.no_build_tagset:
        print('We WILL NOT build the tagset.', file=sys.stderr)
    else:
        print('We WILL build the tagset (for partitioning/traversal).',
              file=sys.stderr)

    print('making nodegraph', file=sys.stderr)
    nodegraph = khmer_args.create_nodegraph(args)

    oxfuncs.build_graph(filenames, nodegraph, args.threads,
                        not args.no_build_tagset)

    print('Total number of unique k-mers: {0}'.format(
        nodegraph.n_unique_kmers()), file=sys.stderr)

    print('saving k-mer nodegraph in', base, file=sys.stderr)
    nodegraph.save(base)

    if not args.no_build_tagset:
        print('saving tagset in', base + '.tagset', file=sys.stderr)
        nodegraph.save_tagset(base + '.tagset')

    info_fp = open(base + '.info', 'w')
    info_fp.write('%d unique k-mers' % nodegraph.n_unique_kmers())

    fp_rate = \
        khmer.calc_expected_collisions(
            nodegraph, args.force, max_false_pos=.15)
    # 0.18 is ACTUAL MAX. Do not change.

    print('false positive rate estimated to be %1.3f' % fp_rate,
          file=sys.stderr)
    print('\nfalse positive rate estimated to be %1.3f' % fp_rate,
          file=info_fp)

    print('wrote to ' + base + '.info and ' + base, file=sys.stderr)
    if not args.no_build_tagset:
        print('and ' + base + '.tagset', file=sys.stderr)

    sys.exit(0)

if __name__ == '__main__':
    main(None)

# vim: set ft=python ts=4 sts=4 sw=4 et tw=79:
