# -*- coding: utf-8 -*-
"""
利用后端接口刷新内存数据，目前暂时包括clearCache和reloadSdata

如下是一条典型的请求：
http://127.0.0.1:8211/root/gateway.action?command=clearCache&path=/app/opbak/20150416_1/update.sql

详细使用可参照：
http://10.6.20.238/project/ALL_GAME/job/show/2f1e71cd-ac45-4692-9db9-343189ceae9f

2015-04-17 Xiaoyu Created
"""
import sys
import os
import time
from fabric.api import env, lcd, local, run, execute, cd, quiet, hosts, put, settings

from utils import set_fabric_common_env, TIMESTAMP, RSYNC, WGET
from game import GameProject
from arg import gameOption, getserverlist


RELEASE_TYPE = 'flush_mem_data'
REMOTE_DIR = '/app/opbak/{}_{}'.format(RELEASE_TYPE, TIMESTAMP)


def mk_remote_dir(remote_dir):
    run(' [ -d {0} ] || mkdir -p {0} '.format(remote_dir))

def get_http_port(gameserver):
    cmd = '''grep 'name="httpPort" type="int"' conf.xml |awk -F[\<\>] '{print $3}' '''
    with cd('/app/{}/backend/apps'.format(gameserver)):
        result = run(cmd) 
    lines = result.splitlines()
    if len(lines) == 1:
        return int(lines[0])
    else:
        raise Exception("Can't get http port using cmd: {}".format(cmd))

def upload_to_resource_server(game, file):
    dir, filename = os.path.split(file)
    resource_dir = '/app/www/{}/{}/{}'.format(game, RELEASE_TYPE, TIMESTAMP) 
    resource_ip = gameOption('www_ssh_ip')
    execute(mk_remote_dir, resource_dir, hosts=[resource_ip])
    with lcd(dir), settings(host_string=resource_ip):
        put(filename, resource_dir)
        put('md5.txt', resource_dir)
    #local('{} {}/{{{},md5.txt}} {}:{}/'.format(RSYNC, dir, filename, resource_ip, resource_dir))

def download_from_resource(game, file):
    remote_dir, filename = os.path.split(file)
    mk_remote_dir(REMOTE_DIR)
    with cd(remote_dir):
        server_name = gameOption('www_header')
        for each_file in [filename, 'md5.txt']:
            run('''{} --header="Host:{}" http://{}/{}/{}/{}/{}'''.format(WGET, server_name, gameOption('www_ip'), game, RELEASE_TYPE, TIMESTAMP, each_file))
        run('dos2unix md5.txt && md5sum -c md5.txt')

class MemoryData(object):
    """
    内存数据库类
    """
    def __init__(self, game, game_pj_obj, debug=True):
        self.game = game
        if not debug: #控制是否输出debug详细信息
            from fabric.api import output
            output.everything = False

        self.game_pj = game_pj_obj

    def flush(self, gameservers, command, table=None, path=None):
       
        locate_gameservers = self.game_pj.transform(gameservers)
        ips = locate_gameservers.keys()
        
        def _flush(gameserver, http_port):
            base_url = 'http://127.0.0.1:{}/root/gateway.action'.format(http_port)

            real_url = '{}?command={}'.format(base_url, command)

            if table is not None:
                real_url += '&tableName={}'.format(table)
            if path is not None:
                real_url += '&path={}'.format(path)

            return run('curl "{}"'.format(real_url))

        def _flush_task():
            if path is not None:
                download_from_resource(self.game, path)

            ret = {}

            for gameserver in locate_gameservers[env.host_string]:
                print('Working on {}...'.format(gameserver))
                http_port = get_http_port(gameserver)
                result = _flush(gameserver, http_port)

                _result = result.lower()

                success_tags = ['succ', 'success']
                if any(each in _result for each in success_tags):
                    ret[gameserver] = (True, result)
                else:
                    ret[gameserver] = (False, result)

            return ret

        result = execute(_flush_task, hosts=ips)

        total = {}
        for each_result in result:
            for each_gameserver in result[each_result]:
                total[each_gameserver] = result[each_result][each_gameserver] 

        return total

    def reloadSdata(self, gameservers, command, version, **kwargs):
        if version.lower() != 'null':
            self.game_pj.upload_backend(version)
        return self.flush(gameservers, 'reloadSdata')

    def clearCache(self, gameservers, command, table=None, ftp_sql_path=None, **kwargs):
        if ftp_sql_path is None:
            remote_sql = None
        else:
            upload_to_resource_server(self.game, ftp_sql_path)
            filename = os.path.basename(ftp_sql_path)
            remote_sql = '{}/{}'.format(REMOTE_DIR, filename)

        return self.flush(gameservers, 'clearCache', table, remote_sql)

def flush_mem_data(args):

    set_fabric_common_env()

    game = args.game
    language = args.language
    command = args.command
    table = args.table[0].replace(' ', '')
    backend_version = args.backend_version[0].replace(' ', '')
    sql_file = args.sql_file[0].replace(' ', '')

    if sql_file.lower() != 'null':
        ftp_sql_path = '/app/online/{}/sql/{}/{}'.format(game, language, sql_file)
    else:
        ftp_sql_path = None


    game_pj = GameProject(game, region=language)
    mem_data = MemoryData(game, game_pj)


    server_info = getserverlist()
    _server_info_dict = {'{}_{}'.format(game, each[0]): each[1] for each in server_info}
    gameservers = ['{}_{}'.format(game, each[0]) for each in server_info]
    print('Game servers below will be updated:\n{}'.format(','.join(gameservers)))

    more_args = {
        'table': table if table.lower() != 'null' else None,
        'ftp_sql_path': ftp_sql_path,
        'version': backend_version
    }

    flush_method = getattr(mem_data, command)
    result = flush_method(gameservers, command, **more_args) 
    print(result)
    if not all(result[each][0] for each in result):
        raise Exception('There are failed servers in the result, please see the result above.')
    print('Done!')

def add_flushMemData_parser(parser):
    """
    添加参数和参数说明
    """
    flushMemData_parser = parser.add_parser("flushMemData", help="刷新内存数据")

    from add_argument import add_serverlist, add_main

    add_main(flushMemData_parser)
    add_serverlist(flushMemData_parser)

    flushMemData_parser.add_argument(
        '-c',
        type=str,
        required=True,
        choices=['reloadSdata', 'clearCache'],
        metavar='CMD',
        dest='command',
        help='flush command, eg: reloadSdata, clearCache'
    )
    flushMemData_parser.add_argument(
        '-t',
        type=str,
        nargs=1,
        default='null',
        metavar='TABLES',
        dest='table',
        help='table names you want to flush, eg: player_name,player_info'
    )
    flushMemData_parser.add_argument(
        '-p',
        type=str,
        nargs=1,
        default='null',
        metavar='/PATH/TO/FILE',
        dest='sql_file',
        help='SQL file path, eg: if the sql is at /sql/cn/20150415_1/change_id.sql, please input 20150415_1/change_id.sql'
    )
    flushMemData_parser.add_argument(
        '-b',
        type=str,
        nargs=1,
        default='null',
        metavar='DIR',
        dest='backend_version',
        help='backend version, eg: game_3-9-1-0'
    )    

    flushMemData_parser.set_defaults(func=flush_mem_data)


