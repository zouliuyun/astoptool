#!/usr/bin/env python
#-*- coding:utf8 -*-
'''
充值中控重启

2015-09-11 Xiaoyun Created
'''
import time,sys,os

#from __future__ import print_function, with_statement

from fabric.api import env, lcd, local, cd, run, put, execute, quiet, hosts, settings, hide

from bible.utils import set_fabric_common_env, TIMESTAMP
from bible.config_reader import ConfigReader
def null(Str):
    if Str == None or str(Str).lower().strip() == "none" or str(Str).strip() == "" or str(Str).lower().strip() == "null":
        Str=""
        return True
    else:
        return False
def update_exec(game, region, version, type):
    if not type:
        print "ERROR: restartType 必须指定!"
        sys.exit(1)
    if not null(version):
        print "上传后端包..."
        local('/app/opbin/rundeck/online.backend -g {} -t {}'.format(game, version))
    conf = ConfigReader(game, region)
    proxy_pay1 = conf.get('proxy_pay1')
    proxy_pay2 = conf.get('proxy_pay2')
    proxy_pay1_ip = conf.get('proxy_pay1_ip')
    proxy_pay2_ip = conf.get('proxy_pay2_ip')
    serverlist = {proxy_pay1:proxy_pay1_ip,proxy_pay2:proxy_pay2_ip}
    print serverlist
    #serverlist = {"twproxy_10001":"113.196.114.26"}
    #serverlist = {"trproxy_10001":"85.195.72.74"}
    if conf.has_option("gateway"):
        gateway = conf.get('gateway')
    for server,ip in serverlist.items():
        if gateway == "":
            with settings(host_string=ip):
                run('export JAVA_HOME=/usr/local/jdk;export LC_ALL=\'en_US.UTF-8\';export LANG=\'en_US.UTF-8\';sh /app/{}_{}/backend/bin/startup.sh {}'.format(game,server,type))
                time.sleep(3)
                cmd = 'ps x -o stime,cmd|grep -v grep | grep -E "java.*{}_{}/"'.format(game,server)
                run(cmd)

        else:
            with settings(host_string=ip,gateway = gateway):
                run('export JAVA_HOME=/usr/local/jdk;export LC_ALL=\'en_US.UTF-8\';export LANG=\'en_US.UTF-8\';sh /app/{}_{}/backend/bin/startup.sh {}'.format(game,server,type))
                time.sleep(3)
                cmd = 'ps x -o stime,cmd|grep -v grep | grep -E "java.*{}_{}/"'.format(game,server)
                run(cmd)
def main(args):
    if args.game and args.language and args.version and args.type:
        set_fabric_common_env()

        game = args.game
        region = args.language
        version = args.version
        type = args.type
        update_exec(game, region, version, type)
        print('Done!')

    else:
        print('Use "-h" to see the command-line options')
        sys.exit(1)

def payProxy_Update(parser):
    """
    添加参数和参数说明
    """
    sub_parser = parser.add_parser("payProxy_Update", help="充值中控更新重启")

    sub_parser.add_argument(
        "-g",
        "--game",
        dest="game",
        required=True,
        help="game, eg: gcld"
    )
    sub_parser.add_argument(
        "-l",
        "--language",
        dest="language",
        required=True,
        help="language, eg: cn, vn"
    )
    sub_parser.add_argument(
        "-v",
        dest="version",
        help="backend version, eg: nhmob_tw_proxy"
    )

    sub_parser.add_argument(
        "-t",
        dest="type",
        required=True,
        help="restart,start,stop"
    )
    sub_parser.set_defaults(func=main)
