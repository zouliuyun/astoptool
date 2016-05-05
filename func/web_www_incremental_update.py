# -*- coding: utf-8 -*-
'''
页游前端增量更新

2015-09-02 Xiaoyu Created
'''

from __future__ import print_function, with_statement

from fabric.api import env, lcd, local, cd, run, put, execute, quiet, hosts, settings, hide

import re

from bible.utils import set_fabric_common_env, TIMESTAMP
from bible.config_reader import ConfigReader

def check_incremental_version(version):
    pattern = '^[a-zA-z0-9_]+_[0-9]+(-[0-9]+){3}$'

    if not re.match(pattern, version):
        raise Exception('Wrong version format: {}'.format(version))

    m = re.match(r'^.*-([0-9]+)$', version)
    if m.group(1) == '0':
        raise Exception('增量更新最后一位应该不为0, 请确认是否是增量更新')

def web_www_incremental_update(game, region, version):
    """
    页游前端增量更新
    """

    check_incremental_version(version)

    conf = ConfigReader(game, region)

    if conf.has_option("gateway"):
        gateway = conf.get('gateway')
        """
        gateway存在且不为空的时候
        """
        if gateway != "":
            #with settings(host_string='ast_hk'):
            #    run('/app/opbin/rundeck/online.frontend_gchw -g {} -t {}'.format(game, version))
            local('/app/opbin/rundeck/online.frontend_gchw -g {} -t {}'.format(game, version))
    else:
        local('/app/opbin/rundeck/online.frontend -g {} -t {}'.format(game, version))

def main(args):
    if args.game and args.language and args.version:
        set_fabric_common_env()

        game = args.game
        region = args.language
        version = args.version
        web_www_incremental_update(game, region, version)
        print('Done!')

    else:
        print('Use "-h" to see the command-line options')
        sys.exit(1)

def add_webWwwIncrementalUpdate_parser(parser):
    """
    添加参数和参数说明
    """
    sub_parser = parser.add_parser("webWwwIncrementalUpdate", help="页游前端增量更新")

    sub_parser.add_argument(
        "-g", 
        "--game", 
        dest="game", 
        required=True, 
        help="game, eg: gcld"
    )
    sub_parser.add_argument(
        "-l", 
        "--region", 
        dest="language", 
        required=True, 
        help="region, eg: cn, vn"
    )
    sub_parser.add_argument(
        "-t",
        dest="version",
        help='frontend version, eg: gcld_1-1-1-10'
    )
    sub_parser.set_defaults(func=main)
