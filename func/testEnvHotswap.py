#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
线上测试环境动更模块

可以参照rundeck：
http://10.6.20.238/project/GCLD/job/show/5c2e67d0-e7de-475b-b779-55ee28b8047c

2015-03-27 Xiaoyu Created
"""

from fabric.api import env, lcd, local, run, execute, cd, quiet, put
import time, argparse, os, re
import sys

from arg import gameOption

TIME = time.strftime("%Y%m%d_%H%M%S")
DATE = time.strftime("%Y%m%d")
RELEASE_TYPE = 'hotswap'
REMOTE_DIR = '/app/opbak/{}_{}'.format(RELEASE_TYPE, TIME)

env.user = 'astd'
env.use_ssh_config = True   # This is important when running under root.
env.connection_attempts = 3
env.disable_known_hosts = True
env.keepalive = 60

def get_test_server_info():
    """
    读取项目配置文件里面的参数
    
    Get all game info. It will return a dict like:
    
    { 'astd_17wan_1' : '10.6.120.23', 
      'astd_37wan_98': '10.4.5.5',
                 .
                 .
                 .
      'astd_37wan_8' : '10.4.5.15' }

    """
    _server_info1 = eval(gameOption('server_list', default='{}'))
    #_server_info2 = eval(gameOption('pay_proxy', default='{}'))

    _server_info = _server_info1.copy()
    #_server_info.update(_server_info2)

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

def check_file(file):
    pattern = r'^/.*/hotswap.zip$'
    file_with_full_path = '/app/online/{}{}'.format(GAME, file)
    file_path = os.path.dirname(file_with_full_path)

    pattern_matched = (re.match(pattern, file), 'Hotswap filename should be hotswap.zip')
    with quiet():
        file_exists = (local('test -f {}'.format(file_with_full_path)).succeeded, '{} does NOT exists on FTP, please check'.format(file))
        md5_exists = (local('test -f {}/md5.txt'.format(file_path)).succeeded, 'md5.txt does NOT exists on FTP, please check')

    for each_check in [pattern_matched, file_exists, md5_exists]:
        if each_check[0]:
            pass
        else:
            raise Exception(each_check[1])

def check_keywords(keywords):
    pattern = r'^\w+(\,\w+){0,}$'
    if re.match(pattern, keywords):
        pass
    else:
        raise Exception('The key {} is not in the allowed pattern'.format(key))

def gameServer_pid(gameServer):
    result_pids = run('''ps x | grep "[j]ava .*\\b%s\\b" | awk '{print $1}' ''' % gameServer)
    pids = result_pids.splitlines()
    if len(pids) == 1:
        return(pids[0])
    else:
        raise Exception('[ERROR] There are more than one java processes running for {}'.format(gameServer))

def _hotswap(file, type, keywords):
    file_with_full_path = '/app/online/{}{}'.format(GAME, file)
    file_path = os.path.dirname(file_with_full_path)
    #local('rsync -aqP {}/{{hotswap.zip,md5.txt}} {}@{}:{}/'.format(file_path, env.user, env.host_string, REMOTE_DIR))
    run('mkdir -p {}'.format(REMOTE_DIR))
    with lcd(file_path):
        put('hotswap.zip', REMOTE_DIR)
        put('md5.txt', REMOTE_DIR)

    with cd(REMOTE_DIR):
        run('dos2unix md5.txt && md5sum -c md5.txt')
        run('unzip -q hotswap.zip')
        run('cd hotswap && chmod +x attach remote update')

    ret_value = {}

    for gameServer in LOCATE_GAME_SRVS[env.host_string]:
        with cd('/app/{}/backend/logs'.format(gameServer)):
            run('echo >start.out')

        with cd('{}/hotswap'.format(REMOTE_DIR)):
            pid = gameServer_pid(gameServer)
            run('./{} {}'.format(type, pid))

        with cd('/app/{}/backend/logs'.format(gameServer)):
            for each_keyword in keywords.split(','):
                with quiet():
                    do_hotswap_success = run('grep --color=never -E -A 20 "reload.*{}" {} | grep --color=never "reload succ"'.format(each_keyword, 'start.out')).succeeded
                if not do_hotswap_success:
                    ret_value[gameServer] = False
                    break
            else:
                ret_value[gameServer] = True

    return ret_value

def hotswap(file, type, keywords):
    #env.parallel = True
    #env.pool_size = 10
    result_for_gameServer = {}
    result = execute(_hotswap, file, type, keywords, hosts=IPS)
    for each_ip in IPS:
        result_for_gameServer.update(result[each_ip])

    print('Hotswap results show as below:')
    for each in result_for_gameServer:
        if result_for_gameServer[each]:
            print('[SUCC] <===> {}'.format(each))
        else:
            print('[FAIL] <===> {}'.format(each))
    
    if not all(result_for_gameServer):
        sys.exit(1)

class Release(object):
    """
    Note
    """
    def __init__(self, args):
        if args.gameServers and args.file and args.keywords and args.type:
            global GAME, IPS, LOCATE_GAME_SRVS, GAME_SRVS
            GAME = args.game
            self.gameServers = args.gameServers[0].replace(' ', '')
            self.file = args.file[0].strip()
            self.keywords = args.keywords[0].strip()
            self.type = args.type[0].strip()

            GAME_SRVS = ['{}_{}'.format(GAME, each) for each in self.gameServers.split(',')]

            all_server_info = get_test_server_info()
            check_game_servers(GAME_SRVS, all_server_info)
            check_file(self.file)
            check_keywords(self.keywords)

            LOCATE_GAME_SRVS = transform_gameServers(GAME_SRVS, all_server_info)
            IPS = LOCATE_GAME_SRVS.keys()

    def hotswap(self):
            print('Game Servers below will be updated: {}'.format(GAME_SRVS))

            hotswap(self.file, self.type, self.keywords)

            print('Done!')

def add_args_for_testEnvHotswap(parser):
    """
    添加参数和参数说明
    """
    parser.add_argument(
        "-g",
        "--game",
        dest="game",
        required=True,
        help="Game project name，eg: gcmob"
    )
    parser.add_argument(
        "-l",
        "--language",
        dest="language",
        required=True,
        help="Language，eg: cn, vn, ft"
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
        metavar='/PATH/TO/FILE',
        dest='file',
        help='The FTP path to the hotswap zip file, eg: /update/xxx/xxx/xx/hotswap.zip'
    )
    parser.add_argument(
        '-k',
        type=str,
        nargs=1,
        metavar='KEYWORDS',
        dest='keywords',
        help='The keywords used to check if hotswap succesfully, eg: key1,key2'
    )
    parser.add_argument(
        '-s',
        type=str,
        nargs=1,
        choices=['update', 'remote'],
        metavar='HOT TYPE',
        dest='type',
        help='The type of hotswap, eg: update or remote'
    )

#def main():
#    parser  = argparse.ArgumentParser(
#        description='Hotswap for test Env'
#    )
#    add_args_for_testEnvHotswap(parser)
#
#    args = parser.parse_args()
#
#    release = Release(args)
#    release.hotswap()
#
#if __name__ == '__main__':
#    main()
