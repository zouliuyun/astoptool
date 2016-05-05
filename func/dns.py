#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dnsapi

这里只是为了方便，将dns添加功能转移到中控机上，
核心的api依然在10.6.196.65:/app/opbin/dns/dnsapi

2015-04-28 Xiaoyu Created Init Create
"""


from fabric.api import env, local, run, execute, cd, quiet, hosts

import argparse

from bible.utils import set_fabric_common_env


DNS_SERVER = '10.6.196.65'

def dnsapi(game, action, domain, line, ip, debug=False):

    if not debug: #控制是否输出debug详细信息 
        from fabric.api import output
        output.everything = False

    @hosts(DNS_SERVER)
    def _dnsapi():
        result = run('/app/opbin/dns/dnsapi -g {game} -a {action} -d {domain} -l {line} -i {ip}'.format(game=game, action=action, domain=domain, line=line, ip=ip))
        print(result)

    execute(_dnsapi)

def print_help():

    with quiet():

        @hosts(DNS_SERVER)
        def _dnsapi():
            result = run('/app/opbin/dns/dnsapi -h')
            print(result)

        execute(_dnsapi)


def dns(args):
    set_fabric_common_env()
    
    if args.detail:
        print_help()
    
    elif args.game and args.action and args.domain and args.line and args.ip:
        dnsapi(args.game, args.action, args.domain, args.line, args.ip)

    else:
        print_help()


def add_parser(parser):
    """
    添加参数和参数说明
    """

    parser.add_argument(
        "-g",
        "--game",
        dest="game",
        help="set game"
    )
    parser.add_argument(
        '-a',
        '--action',
        type=str,
        metavar='ACTION',
        dest='action',
        help='set action'
    )
    parser.add_argument(
        '-d',
        '--domain',
        type=str,
        metavar='DOMAIN',
        dest='domain',
        help='set domain name'
    )
    parser.add_argument(
        '-l',
        '--line',
        type=str,
        metavar='LINE',
        dest='line',
        help='set line type'
    )
    parser.add_argument(
        '-i',
        '--ip',
        type=str,
        metavar='IP',
        dest='ip',
        help='set ip'
    )
    parser.add_argument(
        '-H',
        action='store_true',
        dest='detail',
        help='print more help info and examples'
    )


def main():
    parser  = argparse.ArgumentParser(
        description='dnsapi use dnspod api to add/del/modify/disable records.'
    )
    add_parser(parser)

    args = parser.parse_args()

    dns(args)

if __name__ == '__main__':
    main()
