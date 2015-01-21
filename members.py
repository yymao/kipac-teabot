#!/usr/bin/env python

from argparse import ArgumentParser
parser = ArgumentParser(prog='members.py')
subparsers = parser.add_subparsers(dest='command')

parser_rename = subparsers.add_parser('rename', help='change the arxiv name of a member')
parser_pull = subparsers.add_parser('pull', help='pull the member list from Google Sheets')
parser_update = subparsers.add_parser('update', help='update the arxiv weights for a member')
parser_add = subparsers.add_parser('add', help='add a new member')
parser_print = subparsers.add_parser('print', help='print the arxiv weights for a member')
parser_testers = subparsers.add_parser('testers', help='print all testers')

parser_add.add_argument('arxiv_name')

parser_print.add_argument('arxiv_name')

parser_rename.add_argument('arxiv_name')
parser_rename.add_argument('new_arxiv_name')

parser_update.add_argument('arxiv_name')
parser_update.add_argument('-s', metavar='SCORE', default='1')
parser_update.add_argument('arxiv_id', nargs='+')

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
            if int(row['active'] or 0) + int(row['tester'] or 0) == 0:
                continue
            m = Member(row['arxivname'])
            if not m.has_weights_db():
                print row['arxivname'], 'is a new member, please add', row['arxivname']
                continue
            fo.write(line)

elif args.command=='add':
    m = Member(args.arxiv_name)
    m.create_weights_db()

elif args.command=='update':
    m = Member(args.arxiv_name)
    with m.get_weights_db('w') as d:
        for k in args.arxiv_id:
            if k not in d or float(d[k]) < float(args.s):
                d[k] = args.s

elif args.command=='print':
    m = Member(args.arxiv_name)
    with m.get_weights_db('r') as d:
        for k in d:
            print '%18s    %s'%(k, d[k])

elif args.command=='rename':
    m = Member(args.arxiv_name)
    m.rename(args.new_arxiv_name)

elif args.command=='testers':
    with open(member_list_path, 'r') as f:
        header = f.next().strip().split(',')
        for line in f:
            row = dict(zip(header, line.strip().split(',')))
            if int(row['tester'] or 0):
                print row['name'], '<%s>,'%(row['email'])

