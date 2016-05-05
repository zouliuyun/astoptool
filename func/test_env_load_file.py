# -*- coding: utf-8 -*-
"""
线上测试环境上传文件模块

可以参照rundeck：
http://10.6.20.238/project/ALL_GAME/job/show/8a0a3483-147a-48bf-8586-35f7835cdd23

2015-04-27 Xiaoyu Created
"""

from fabric.api import env, local, run, execute, cd, quiet, hosts, put, get
import time, argparse, os, re
import sys

from arg import gameOption
from utils import set_fabric_common_env, TIMESTAMP
from xiaoyu_utils import transform_gameservers, check_game_servers

RELEASE_TYPE = 'upload_file'
REMOTE_DIR = '/app/opbak/{}_{}'.format(RELEASE_TYPE, TIMESTAMP)

def utf8_check(file):
    result = local('file {}'.format(file), capture=True)
    if not 'UTF-8' in result:
        print('[ERROR] File: {} is NOT UTF-8 format.'.format(file))
        sys.exit(1)
    if 'with BOM' in result:
        bom_help = """
        有些编辑器，比如M$ Windows的记事本，在创建UTF8编码文件时会在头部添加一个不可见字符。这个字符可以通过vim查看到，而且如果是一个php文件，php4、php5在解析时均会有输出。
        原来这个被称作BOM(Byte Order Mark)的不可见字符，是Unicode用来标识内部编码的排列方式的，在UTF-16、UTF-32编码里它是必需的，而在UTF-8里是可选的。
        因此，才会出现有的编辑器在文件头部添加添加BOM、而有的语法解析器又不作处理的的混乱情况。
        BOM可能会引起某些严重问题，请重新保存为不带BOM的UTF-8格式。
        """
        print('[ERROR] BOM(Byte Order Mark) detected in the file: {}'.format(file))
        print(bom_help)
        sys.exit(1)

def md5_check(single_file):
    dir, name = os.path.split(single_file)
    with lcd(dir):
        local('dos2unix md5.txt')
        local('md5sum -c md5.txt')

def ftp_file_check(file):
    """
    File should be a full path to file
    """
    dir, filename = os.path.split(file)

    if os.path.isfile(file):
        #if file.endswith(('.properties', '.txt')):
        if file.endswith(('.properties')):
            utf8_check(file)
    else:
        raise Exception("File: {} doesn't exist on FTP".format(file))

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

def upload(local_path, remote_path, ip):

    @hosts(ip)
    def _inner_task():
        run('mkdir -p {}'.format(remote_path))
        put(local_path, remote_path)

    execute(_inner_task)

def file_name_consistence_check(local_file, remote_file):
    filename1 = os.path.basename(local_file)
    filename2 = os.path.basename(remote_file)

    if filename1 != filename2:
        print('The local file name is different from the remote_file, this is NOT allowed')
        sys.exit(1)

def replace_file(game_server, remote_file):
    backup_dir = '{}/{}'.format(REMOTE_DIR, game_server)
    run('mkdir -p {}'.format(backup_dir))
    full_path_remote_file = '/app/{}/{}'.format(game_server, remote_file)

    dir, filename = os.path.split(full_path_remote_file)

    run('[ -d {0} ] || mkdir -p {0}'.format(dir))
    with cd(dir):
        run('[ -f {0} ] && cp {0} {1}/ || echo "{0} NOT exists, will not do backup"'.format(filename, backup_dir))
        run('cp {0}/{1} ./{1}'.format(REMOTE_DIR, filename))
 
def load_file(game_servers, local_file, remote_file, load_type='upload'):
    test_server_info = get_test_server_info(GAME)
    check_game_servers(game_servers, test_server_info)
    
    locate_game_servers = transform_gameservers(game_servers, test_server_info)

    ips = locate_game_servers.keys()

    @hosts(ips)
    def _upload_file():
        upload(local_file, REMOTE_DIR, env.host_string)
        for game_server in locate_game_servers[env.host_string]:
            replace_file(game_server, remote_file)

    @hosts(ips)
    def _download_file():
        for game_server in locate_game_servers[env.host_string]:
            local_path = '{}/{}/'.format(local_root_path, game_server)
            local('su - astd -c "mkdir -p {}"'.format(local_path))
            target_file = '/app/{}/{}'.format(game_server, remote_file)
            with quiet():
                target_file_exists = run('test -f {}'.format(target_file)).succeeded
            
            if target_file_exists:
                get(target_file, local_path)
            else:
                raise Exception('File {} NOT exists on {}'.format(target_file, game_server))
        
        local('chown -R astd.astd {}'.format(local_root_path))

    if load_type == 'upload':
        ftp_file_check(local_file)
        file_name_consistence_check(local_file, remote_file)
        execute(_upload_file)
        print('{} was uploaded to {} successfully.'.format(local_file, game_servers))

    elif load_type == 'download':
        ftp_path = 'download/{}/{}'.format(GAME, TIMESTAMP)
        local_root_path = '/app/online/{}'.format(ftp_path)
        execute(_download_file)
        print('Downloaded remote file: {} to FTP: {}/'.format(remote_file, ftp_path))


def main(args):
    global GAME

    set_fabric_common_env()

    GAME = args.game
    language = args.language
    load_type = args.load_type

    gateway = args.gateway
    if gateway != 'No':
        env.gateway = gateway

    local_file = '/app/online/{}/{}'.format(GAME, args.local_file.strip('/'))
    remote_file = args.remote_file.strip('/')

    game_servers = ['{}_{}'.format(GAME, each) for each in args.gameservers.split(',')]

    load_file(game_servers, local_file, remote_file, load_type=load_type)

    print('Done!')


def add_testEnvLoadFile_parser(parser):
    """
    添加参数和参数说明
    """

    sub_parser = parser.add_parser("testEnvLoadFile", help="测试环境上传/下载文件")

    from add_argument import add_main

    add_main(sub_parser)

    sub_parser.add_argument(
        '-t',
        type=str,
        required=True,
        metavar='GameServers',
        dest='gameservers',
        help='game servers you want to upload file to, eg: ast_10001,ast_10002'
    )
    sub_parser.add_argument(
        '-r',
        type=str,
        required=True,
        metavar='PATH',
        dest='remote_file',
        help='remote relative path to file, eg: backend/apps/conf.xml'
    )
    sub_parser.add_argument(
        '-f',
        type=str,
        default='null',
        metavar='/PATH/TO/FILE',
        dest='local_file',
        help='FTP path to file, eg: /update/20150506_1/conf.xml'
    )
    sub_parser.add_argument(
        '-d',
        type=str,
        metavar='upload/download',
        choices=['upload', 'download'],
        default='upload',
        dest='load_type',
        help='upload or download?'
    )
    sub_parser.add_argument(
        '--gateway',
        type=str,
        default='No',
        dest='gateway',
        help='gateway for ssh connection, eg: ast_hk'
    )
    sub_parser.set_defaults(func=main)


