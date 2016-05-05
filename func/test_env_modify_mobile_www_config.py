# -*- coding: utf-8 -*-
"""
修改手游前端测试环境中version.lua的内容

可以参照rundeck：


2015-07-24 Xiaoyu Created
"""
from __future__ import print_function, with_statement

import sys
import time
import re
import os

from fabric.api import env, lcd, local, cd, run, put, execute, quiet, hosts, settings, hide

from bible.utils import set_fabric_common_env, TIMESTAMP
from bible.config_reader import ConfigReader
from bible.config import Config

RELEASE_TYPE = 'modify_mobile_www_config'
REMOTE_DIR = '/app/opbak/{}_{}'.format(RELEASE_TYPE, TIMESTAMP)

class MConfig(Config):
    """
    一个特殊一点的Config类
    """
    def __init__(self, filename, remote_dir=REMOTE_DIR):
        self.filename = filename
        self.dir = run('pwd')

        with quiet():
            has_the_file = run('test -f {}'.format(filename)).succeeded

        if not has_the_file:
            raise Exception('File {}/{} NOT exists'.format(self.dir, filename))
        
        tmp_tag = self.filename.split('/')[0]
        backup_dir = '{}/{}'.format(remote_dir, tmp_tag)
        run('[ -d {0} ] || mkdir -p {0}'.format(backup_dir))
        run('cp {} {}/'.format(self.filename, backup_dir))


def modify_mobile_www_config(game, region, scopes, filename, option_name, option_value):

    conf = ConfigReader(game, region)
    ip = conf.get("mobile_www_ip")

    if conf.has_option("mobile_www_port"):
        """
        如果前端资源服务器限制了ssh连接端口的话，修改Fabric的连接到该host的端口
        """
        port = conf.getint("mobile_www_port")     
        if port:
            ip = '{}:{}'.format(ip, port)

    root_dir = conf.get("mobile_www_root_test")

    @hosts(ip)
    def _modify_mobile_www_config():
        for each_scope in scopes:
            with cd(root_dir):
                _filename = '{}/{}'.format(each_scope, filename)
                config_file = MConfig(_filename)
                config_file.modify(key=option_name, value=option_value)

    execute(_modify_mobile_www_config)

def main(args):
    if args.game and args.language and args.filename and args.scope and args.key and args.value:
        set_fabric_common_env()

        gateway = args.gateway
        if gateway != 'No':
            env.gateway = gateway

        game = args.game
        region = args.language
        scopes = args.scope.strip().split(',')
        filename = args.filename.strip()
        option_name = args.key
        option_value = args.value

        modify_mobile_www_config(game, region, scopes, filename, option_name, option_value)

        print('Done!')

    else:
        print('Use "-h" to see the command-line options')
        sys.exit(1)

def add_testEnvModifyMobileWwwConfig_parser(parser):
    """
    添加参数和参数说明
    """
    sub_parser = parser.add_parser("testEnvModifyMobileWwwConfig", help="手游前端测试环境配置文件修改")

    sub_parser.add_argument(
        "-g", 
        "--game", 
        dest="game", 
        required=True, 
        help="game, eg: gcmob"
    )
    sub_parser.add_argument(
        "-l", 
        "--region", 
        dest="language", 
        required=True, 
        help="region, eg: cn, vn, ft"
    )
    sub_parser.add_argument(
        '-k',
        type=str,
        dest='key',
        help='The name of the key that you want to change in the file'
    )
    sub_parser.add_argument(
        '-v',
        type=str,
        dest='value',
        help='The value or content for the key'
    )
    sub_parser.add_argument(
        '-f',
        type=str,
        dest='filename',
        help='the config file name, eg: version.lua'
    )
    sub_parser.add_argument(
        '-s',
        type=str,
        dest='scope',
        help='the scope you want to release, eg: jailbreak,appstore'
    )
    sub_parser.add_argument(
        '--gateway',
        type=str,
        default='No',
        dest='gateway',
        help='gateway for ssh connection, eg: ast_hk'
    )
    sub_parser.set_defaults(func=main)


