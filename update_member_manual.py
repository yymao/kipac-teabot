#!/usr/bin/env python

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument('arxiv_name')
parser.add_argument('-s', metavar='SCORE', default='1')
parser.add_argument('arxiv_id', nargs='+')
args = parser.parse_args()

from database import model_dir
import anydbm

d = anydbm.open('%s/%s'%(model_dir, args.arxiv_name), 'c')
for k in args.arxiv_id:
    d[k] = args.s
d.close()

