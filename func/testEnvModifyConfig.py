# -*- coding: utf-8 -*-
"""
线上测试环境配置文件修改脚本(配置文件仅限/backend/apps/下的*.properties)，
请使用-h参数查看脚本帮助信息。

可以参照rundeck：
http://10.6.20.238/project/GCLD/job/show/7554058b-a563-4eac-b0a8-d8cdcdf6f6d2

2015-03-09 Xiaoyu Created
"""

from fabric.api import env, local, run, execute, cd, quiet
import time, argparse, os, re

from arg import gameOption
from bible.config import Config

TIME = time.strftime("%Y%m%d_%H%M%S")
RELEASE_TYPE = 'modify_config'
REMOTE_DIR = '/app/opbak/{}_{}'.format(RELEASE_TYPE, TIME)

env.user = 'astd'
env.use_ssh_config = True   # This is important when running under root.
env.connection_attempts = 3
env.disable_known_hosts = True
env.keepalive = 60

def get_test_server_info():
    """
    读取项目配置文件里面的参数
    
    Get all game info. It will get a dict like:
    
    { 'astd_17wan_1' : '10.6.120.23', 
      'astd_37wan_98': '10.4.5.5',
                 .
                 .
                 .
      'astd_37wan_8' : '10.4.5.15' }

    """
    _server_info = {}
    for each_part in ['server_list', 'pay_proxy', 'voice']:
        tmp_value = eval(gameOption(each_part, default='{}'))
        _server_info.update(tmp_value)

    server_info = {'{}_{}'.format(GAME, each): _server_info[each] for each in _server_info}
    return server_info

def transform_gameServers(gameServers, all_server_info):
    """
    Transform funcion. 
    eg: it will transformat from 
        ['astd_37wan_2', 'astd_51wan_99', 'astd_uoyoo_90']
    to
        {
            '10.6.20.1':['astd_37wan_2', 'astd_51wan_99'], 
            '10.6.20.2':['astd_uoyoo_90']
        }
    """
    host_ips = list(set([ all_server_info[each] for each in gameServers ]))
    locate_game_servers = { each:[] for each in host_ips }
    for each in gameServers:
        locate_game_servers[all_server_info[each]].append(each)
    return locate_game_servers

def check_game_servers(gameServers, all_server_info):
    all_game_servers = all_server_info.keys()
    for each_gameServer in gameServers:
        if each_gameServer in all_game_servers:
            pass
        else:
            raise Exception('GameServer: {} NOT in known list'.format(each_gameServer))

def check_filename(filename):
    pattern = r'^.+\.properties$'
    if re.match(pattern, filename):
        pass
    else:
        print('Sorry, you can only modify the *.properties.')
        raise Exception('{} is not allowed to modify'.format(filename))

def check_key_name(key):
    pattern = r'^[a-zA-Z0-9\.]+$'
    if re.match(pattern, key):
        pass
    else:
        raise Exception('The key {} is not in the allowed pattern'.format(key))

def modify_file(filename, operation, key, value, comment='null'):
    for gameServer in LOCATE_GAME_SRVS[env.host_string]:
        with cd('/app/{}/backend/apps'.format(gameServer)):
            conf = Config(filename)
            operate_method = getattr(conf, operation)
            operate_method(key, value, comment)

class Release(object):
    """
    Note
    """
    def __init__(self, args):
        if args.gameServers and args.filename and args.key and args.value and args.operation:
            global GAME, IPS, LOCATE_GAME_SRVS, GAME_SRVS
            GAME = args.game
            self.gameServers = args.gameServers[0].replace(' ', '')
            self.filename = args.filename[0].strip()
            self.key = args.key[0].strip()
            self.value = args.value[0].strip()
            self.operaition = args.operation[0].strip()
            self.comment = args.comment[0].strip()

            gateway = args.gateway
            if gateway != 'No':
                env.gateway = gateway

            GAME_SRVS = ['{}_{}'.format(GAME, each) for each in self.gameServers.split(',')]

            all_server_info = get_test_server_info()
            check_game_servers(GAME_SRVS, all_server_info)
            check_filename(self.filename)
            check_key_name(self.key)

            LOCATE_GAME_SRVS = transform_gameServers(GAME_SRVS, all_server_info)
            IPS = LOCATE_GAME_SRVS.keys()

    def run(self):
            print('Game Servers below will be updated: {}'.format(GAME_SRVS))

            execute(modify_file, self.filename, self.operaition, self.key, self.value, comment=self.comment, hosts=IPS)

            print('Done!')

def add_args_for_testEnvModifyConfig(parser):
    """
    添加参数和参数说明
    """
    parser.add_argument(
        "-g",
        "--game",
        dest="game",
        required=True,
        help="Game project name，eg:gcmob"
    )
    parser.add_argument(
        "-l",
        "--language",
        dest="language",
        required=True,
        help="Language，eg:cn, vn, ft"
    )
    parser.add_argument(
        '-t',
        type=str,
        nargs=1,
        metavar='GameServers',
        dest='gameServers',
        help='Game Servers, eg: yaowan_58,37wan_8'
    )
    parser.add_argument(
        '-f',
        type=str,
        nargs=1,
        metavar='FILENAME',
        dest='filename',
        help='The filename under /backend/apps/, that you want to modify'
    )
    parser.add_argument(
        '-k',
        type=str,
        nargs=1,
        metavar='KEY',
        dest='key',
        help='The name of the key that you want to change in the file'
    )
    parser.add_argument(
        '-v',
        type=str,
        nargs=1,
        metavar='VALUE',
        dest='value',
        help='The value or content for the key'
    )
    parser.add_argument(
        '-c',
        type=str,
        nargs=1,
        metavar='COMMENT',
        dest='comment',
        default=['null'],
        help='The comment for the key'
    )
    parser.add_argument(
        '-o',
        type=str,
        nargs=1,
        choices=['add', 'modify', 'delete'],
        metavar='OPERATION',
        dest='operation',
        help='The operation, eg: add, modify, delete'
    )
    parser.add_argument(
        '--gateway',
        type=str,
        default='No',
        dest='gateway',
        help='gateway for ssh connection, eg: ast_hk'
    )
