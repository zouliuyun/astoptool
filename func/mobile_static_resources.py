# -*- coding:utf-8 -*-
"""
手游特殊静态资源更新

2015-07-15 Xiaoyu Init create.
"""
from __future__ import print_function, with_statement

import sys
import time
import re
import os

from fabric.api import env, lcd, local, cd, run, put, execute, quiet, hosts, settings, hide

from bible.utils import set_fabric_common_env, TIMESTAMP
from bible.config_reader import ConfigReader


def remote_file_exists(file):
    with quiet():
        return run('test -f "{}"'.format(file)).succeeded

def remote_dir_exists(file):
    with quiet():
        return run('test -d "{}"'.format(file)).succeeded

def remote_mkdir(dir):
    run('[[ -d {0} ]] || mkdir -p {0}'.format(dir))
    
def rsync_to_backup(game, region):
    print("等待同步资源目录到备用服务器...")
    sys.stdout.flush()
    time.sleep(20)
    config = ConfigReader(game, region)
    rsync_module = config.get("rsync_module")
    rsync_root = config.get("rsync_root")
    rsync_backup_ip = config.get("rsync_backup_ip")

    if rsync_module == "" or rsync_root == "" or rsync_backup_ip == "" :
        raise Exception('rsync config is not proper in the game config file')

    with cd(rsync_root), settings(user='root'), hide("stdout"):
        run('''rsync -art -R --delete --out-format="%n" --password-file=/etc/rsyncd.secret ./ {}::{}'''.format(rsync_backup_ip, rsync_module))
     
def test_env_mobile_static_resources(game, region, component, root_dir, ip):

    @hosts(ip)
    def _test_env_mobile_static_resources():
        """
        Inner Fabric task 
        """
        ftp_resource_dir = "/app/online/{}/frontend/{}/{}".format(game, region, component)
        remote_temp_dir = "/app/opbak/test_mobile_static_resources_release/{}_{}_{}_{}".format(game, region, component, TIMESTAMP)
        remote_backup_dir = "/app/opbak/test_mobile_static_resources_release/backup_{}_{}_{}_{}".format(game, region, component, TIMESTAMP)

        #本地检查md5
        with lcd(ftp_resource_dir):
            local("dos2unix md5.txt >/dev/null 2>&1")
            local("chown virtual_user.virtual_user md5.txt")
            local("md5sum -c md5.txt >/dev/null")
    
        #新建远程临时资源目录
        remote_mkdir(remote_temp_dir)
    
        #上传zip包跟md5.txt
        component_zip_file = '{}.zip'.format(component)
        print('开始上传 {}...'.format(component_zip_file))
        sys.stdout.flush()
        with lcd(ftp_resource_dir):
            put(component_zip_file, remote_temp_dir)
            put('md5.txt', remote_temp_dir)
    
        #再次检查md5
        with cd(remote_temp_dir):
            run('dos2unix md5.txt')
            run('md5sum -c md5.txt')
            run("unzip -o -q {}".format(component_zip_file))

            #检测zip中是不是存在该component的目录
            run('test -d "{}"'.format(component))

        static_resources_dir = '{}/static_resources'.format(root_dir)
        remote_mkdir(static_resources_dir)
    
        with cd(static_resources_dir):
            if remote_dir_exists(component):
                run('mkdir -p {}'.format(remote_backup_dir))
                run('mv {} {}/'.format(component, remote_backup_dir))
        
        with cd(remote_temp_dir):
            run('cp -r {} {}/'.format(component, static_resources_dir))
   
        #清理FTP上的目录和文件
        local("rm -rf /app/online/{}/frontend/{}/{}".format(game, region, component))

    execute(_test_env_mobile_static_resources)

def prod_env_mobile_static_resources(game, region, component, root_dir_prod, root_dir_test, ip):

    @hosts(ip)
    def _prod_env_mobile_static_resources():
        #备份
        remote_backup_dir = "/app/opbak/prod_mobile_static_resources_release/{}_{}_{}".format(game, region, TIMESTAMP)
        remote_mkdir(remote_backup_dir)

        static_resources_dir_prod = '{}/static_resources'.format(root_dir_prod)
        remote_mkdir(static_resources_dir_prod)

        static_resources_dir_test = '{}/static_resources'.format(root_dir_test)

        with cd(static_resources_dir_prod):
            if remote_dir_exists(component):
                run('cp -r {} {}/'.format(component, remote_backup_dir))

        #同步新版本的目录到生产环境
        run('rsync -aqP --delete {test_dir}/{component}/ {prod_dir}/{component}/'.format(test_dir=static_resources_dir_test, prod_dir=static_resources_dir_prod, component=component))
    
        #等待备份服务器同步完毕, 再接着更新
        conf_wait_rsync = ConfigReader(game, region)
        if conf_wait_rsync.has_option("mobile_www_wait_rsync"):
            wait_rsync = conf_wait_rsync.getboolean("mobile_www_wait_rsync")
            if wait_rsync:
                rsync_to_backup(game, region)

    execute(_prod_env_mobile_static_resources)

def mobile_static_resources(game, region, component, game_env):
    """
    总的调度函数，负责读取一些参数，然后传给prod或test的函数

    """

    conf = ConfigReader(game, region)

    ip = conf.get("mobile_www_ip")

    if conf.has_option("mobile_www_port"):
        """
        如果前端资源服务器限制了ssh连接端口的话，修改Fabric的连接到该host的端口
        """
        port = conf.getint("mobile_www_port")     
        if port:
            ip = '{}:{}'.format(ip, port)

    if game_env == 'test':
        root_dir = conf.get("mobile_www_root_test")
        test_env_mobile_static_resources(game, region, component, root_dir, ip)
    elif game_env == 'prod':
        root_dir_prod = conf.get("mobile_www_root")
        root_dir_test = conf.get("mobile_www_root_test")
        prod_env_mobile_static_resources(game, region, component, root_dir_prod, root_dir_test, ip)


def main(args):
    if args.game and args.language and args.component and args.game_env:
        set_fabric_common_env()

        game = args.game
        region = args.language
        component = args.component.strip()
        game_env = args.game_env

        mobile_static_resources(game, region, component, game_env)

        print('Done!')

    else:
        print('Use "-h" to see the command-line options')
        sys.exit(1)

def add_mobileStaticResources_parser(parser):
    """
    添加参数和参数说明
    """
    sub_parser = parser.add_parser("mobileStaticResources", help="手游前端资源动更")

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
        '--env',
        type=str,
        dest='game_env',
        choices=['prod', 'test'],
        help='Production Environment or Test Environment?'
    )
    sub_parser.add_argument(
        '-t',
        type=str,
        dest='component',
        required=True,
        help='component name, eg: activity_post'
    )
    sub_parser.set_defaults(func=main)

