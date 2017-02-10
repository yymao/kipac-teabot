#!/usr/bin/env python

from argparse import ArgumentParser
parser = ArgumentParser(prog='members.py')
subparsers = parser.add_subparsers(dest='command')

parser_rename = subparsers.add_parser('rename', help='change the arxiv name of a member')
parser_pull = subparsers.add_parser('pull', help='pull the member list from Google Sheets')
parser_add = subparsers.add_parser('add', help='add a new member')
parser_print = subparsers.add_parser('print', help='print the arxiv weights for a member')
parser_testers = subparsers.add_parser('subscribers', help='print all subscribers')

parser_add.add_argument('arxiv_name')

parser_print.add_argument('arxiv_name')

parser_rename.add_argument('arxiv_name')
parser_rename.add_argument('new_arxiv_name')

args = parser.parse_args()

from urllib import urlopen
from Member import Member
from secrets import member_list_url, member_list_path

if args.command=='pull':
    with open(member_list_path, 'w') as fo:
        f = urlopen(member_list_url)
        line = f.next()
        fo.write(line)
        header = line.strip().split(',')
        for line in f:
            row = dict(zip(header, line.strip().split(',')))
            m = Member(row['arxivname'])
            if not m.has_weights_db():
                m.create_weights_db()
            fo.write(line)

elif args.command=='add':
    m = Member(args.arxiv_name)
    m.create_weights_db()

elif args.command=='print':
    m = Member(args.arxiv_name)
    with m.get_weights_db('r') as d:
        for k in d:
            print '%18s    %s'%(k, d[k])

elif args.command=='rename':
    m = Member(args.arxiv_name)
    m.rename(args.new_arxiv_name)

elif args.command=='subscribers':
    with open(member_list_path, 'r') as f:
        header = f.next().strip().split(',')
        for line in f:
            row = dict(zip(header, line.strip().split(',')))
            if Member(row['arxivname']).has_prefs():
                print row['name'], '<%s>,'%(row['email'])

