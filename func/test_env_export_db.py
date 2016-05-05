# -*- coding: utf-8 -*-
"""
线上测试环境导出DB模块

可以参照rundeck：


2015-04-27 Xiaoyu Created
"""

from fabric.api import env, local, run, execute, cd, quiet, hosts, get
import time, argparse, os, re
import sys

from arg import gameOption
from utils import set_fabric_common_env, TIMESTAMP
from xiaoyu_utils import transform_gameservers, check_game_servers

RELEASE_TYPE = 'export_db'
REMOTE_DIR = '/app/opbak/{}_{}'.format(RELEASE_TYPE, TIMESTAMP)

def get_test_server_info(game):
    """
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

    server_info = {'{}_{}'.format(game, each): _server_info[each] for each in _server_info}
    return server_info

def export_db(game_servers, export_type='data'):
    test_server_info = get_test_server_info(GAME)
    check_game_servers(game_servers, test_server_info)
    
    locate_game_servers = transform_gameservers(game_servers, test_server_info)

    ips = locate_game_servers.keys()

    ftp_path = 'download/{}/{}'.format(GAME, TIMESTAMP)
    local_root_path = '/app/online/{}'.format(ftp_path)

    @hosts(ips)
    def _export_db():
        for game_server in locate_game_servers[env.host_string]:
            local_path = '{}/{}/'.format(local_root_path, game_server)
            local('su - astd -c "mkdir -p {}"'.format(local_path))

            run('mkdir -p {}'.format(REMOTE_DIR))

            sql_name = '{}.sql.rb{}'.format(game_server, TIMESTAMP)

            if export_type == 'no-data':
                run('pandora --dump -R --opt -d {} >{}/{}'.format(game_server, REMOTE_DIR, sql_name))
            elif export_type == 'data':
                run('pandora --dump -R --opt {} >{}/{}'.format(game_server, REMOTE_DIR, sql_name))

            with cd(REMOTE_DIR):
                run('tar zcf {0}.tgz {0}'.format(sql_name))

            target_file = '{}/{}.tgz'.format(REMOTE_DIR, sql_name)
            get(target_file, local_path)
        
        local('chown -R astd.astd {}'.format(local_root_path))

    print('Start dumping db...')
    sys.stdout.flush()
    execute(_export_db)
    print('Downloaded db to FTP: {}/'.format(ftp_path))


def main(args):
    global GAME

    set_fabric_common_env()

    gateway = args.gateway
    if gateway != 'No':
        env.gateway = gateway

    GAME = args.game
    language = args.language
    export_type = args.export_type

    game_servers = ['{}_{}'.format(GAME, each) for each in args.gameservers.split(',')]

    export_db(game_servers, export_type=export_type)

    print('Done!')


def add_testEnvExportDB_parser(parser):
    """
    添加参数和参数说明
    """

    sub_parser = parser.add_parser("testEnvExportDB", help="测试环境数据库导出")

    from add_argument import add_main

    add_main(sub_parser)

    sub_parser.add_argument(
        '-t',
        type=str,
        required=True,
        metavar='GameServers',
        dest='gameservers',
        help='game servers you want to do with, eg: ast_10001,ast_10002'
    )
    sub_parser.add_argument(
        '-d',
        type=str,
        choices=['data', 'no-data'],
        default='export_type',
        dest='export_type',
        help='export DB with data or with no-data?'
    )
    sub_parser.add_argument(
        '--gateway',
        type=str,
        default='No',
        dest='gateway',
        help='gateway for ssh connection, eg: ast_hk'
    )

    sub_parser.set_defaults(func=main)


