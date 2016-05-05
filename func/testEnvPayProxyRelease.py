# -*- coding: utf-8 -*-
"""
线上测试环境充值中控版本更新脚本(含后端上传，更改后端版本目录，重启功能)，
请使用-h参数查看脚本帮助信息。

可以参照rundeck：
http://10.6.20.238/project/GCLD/job/show/ca6ba08a-760f-4a47-bed8-64b55ca88a68

2015-02-10 Xiaoyu Created
"""

from fabric.api import env, local, run, execute, cd
import time, argparse, os, re

from arg import gameOption

TIME = time.strftime("%Y%m%d_%H%M%S")
DATE = time.strftime("%Y%m%d")

env.user = 'astd'
env.use_ssh_config = True   # This is important when running under root.
env.connection_attempts = 3
env.disable_known_hosts = True
env.keepalive = 60

def get_all_info():
    """
    Get all game info. It will get a dict like:
    
    { 'astd_17wan_1' : '10.6.120.23', 
      'astd_37wan_98': '10.4.5.5',
                 .
                 .
                 .
      'astd_37wan_8' : '10.4.5.15' }

    """
    info_dict = test_pay_proxy_info()
    return info_dict

def test_pay_proxy_info():
    _server_info = {}
    for each_part in ['pay_proxy', 'voice']:
        tmp_value = eval(gameOption(each_part, default='{}'))
        _server_info.update(tmp_value)

    server_info = {'{}_{}'.format(GAME, each): _server_info[each] for each in _server_info}
    return server_info

def transform_gameServers(gameServers):
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
    all_info = get_all_info()
    host_ips = list(set([ all_info[each] for each in gameServers ]))
    locate_game_servers = { each:[] for each in host_ips }
    for each in gameServers:
        locate_game_servers[all_info[each]].append(each)
    return locate_game_servers

def check_game_servers(gameServers):
    all_info = get_all_info()
    all_game_servers = all_info.keys()
    for each_gameServer in gameServers:
        if each_gameServer in all_game_servers:
            pass
        else:
            raise Exception('GameServer: {} NOT in known list'.format(each_gameServer))

def check_end_version(version):
    if version.lower() != 'no':
        pattern = '^%stest_proxy_[0-9]+(-[0-9]+){3}$' % GAME
        if re.match(pattern, version):
            pass
        else:
            raise Exception('Wrong version format: {}'.format(version))

def stop_gameServer(gameServer):
    run(''' /bin/bash /app/{}/backend/bin/startup.sh stop '''.format(gameServer), warn_only=True)

def start_gameServer(gameServer):
    run(''' set -m; /bin/bash /app/{}/backend/bin/startup.sh start '''.format(gameServer))

def upload_backend(version):
    local('''/app/opbin/rundeck/online.backend -t {} -g {}'''.format(version, GAME))

def upload(bVer_4, bUpload):
    if bVer_4.lower() != 'no' and bUpload == 'Yes':
        print('Start upload backtend...')
        upload_backend(bVer_4)

def update(restart='No'):
    for gameServer in LOCATE_GAME_SRVS[env.host_string]:
        if restart == 'Yes':
            stop_gameServer(gameServer)
        if restart == 'Yes':
            start_gameServer(gameServer)

class Release(object):
    """
    Note
    """
    def __init__(self, args):
        if args.gameServers and args.component:
            global GAME, IPS, LOCATE_GAME_SRVS, GAME_SRVS
            GAME = args.game
            self.gameServers = args.gameServers[0].replace(' ', '')
            self.restart = args.restart[0]
            self.bUpload = args.bUpload[0]
            self.component = args.component[0]

            gateway = args.gateway
            if gateway != 'No':
                env.gateway = gateway

            self.bVer_4 = '{}test_{}'.format(GAME, self.component)

            GAME_SRVS = ['{}_{}'.format(GAME, each) for each in self.gameServers.split(',')]
            check_game_servers(GAME_SRVS)

            LOCATE_GAME_SRVS = transform_gameServers(GAME_SRVS)
            IPS = LOCATE_GAME_SRVS.keys()

    def run(self):
            print('Servers below will be updated: {}'.format(GAME_SRVS))

            upload(self.bVer_4, self.bUpload)
            execute(update, restart=self.restart, hosts=IPS)

            print('Done!')

def add_args_for_testEnvPayProxyRelease(parser):
    """
    添加参数和参数说明
    """
    parser.add_argument(
        "-g",
        "--game",
        dest="game",
        required=True,
        help="指定项目名称，比如:gcmob"
    )
    parser.add_argument(
        "-l",
        "--language",
        dest="language",
        required=True,
        help="指定语言，比如:cn, vn, ft"
    )
    parser.add_argument(
        '-t',
        type=str,
        nargs=1,
        metavar='GameServers',
        dest='gameServers',
        help='Game Servers, eg: {0}_yaowan_58,{0}_37wan_8'.format('game')
    )
    parser.add_argument(
        '--gateway',
        type=str,
        default='No',
        dest='gateway',
        help='gateway for ssh connection, eg: ast_hk'
    )
    parser.add_argument(
        '-r',
        type=str,
        choices=['Yes', 'No'],
        default=['No'],
        nargs=1,
        metavar='Yes/No',
        dest='restart',
        help='Need resart?, eg: Yes/No'
    )
    parser.add_argument(
        '--b-upload',
        type=str,
        choices=['Yes', 'No'],
        default=['No'],
        nargs=1,
        metavar='Yes/No',
        dest='bUpload',
        help='Backend Upload?, eg: Yes/No'
    )
    parser.add_argument(
        '-c',
        type=str,
        default=['proxy'],
        nargs=1,
        metavar='COMPONENT',
        dest='component',
        help='Component, eg: proxy'
    )
 
