#!/usr/bin/env python

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument('merge_to_name')
parser.add_argument('names_to_merge', nargs='+')
args = parser.parse_args()

from database import model_dir
import anydbm

d = anydbm.open('%s/%s'%(model_dir, args.merge_to_name), 'c')
for name in args.names_to_merge:
    d1 = anydbm.open('%s/%s'%(model_dir, name), 'r')
    d.update(d1)
    d1.close()
d.close()

