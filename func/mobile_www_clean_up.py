# -*- coding: utf-8 -*-
"""
手游前端资源清理。

分为两种清理:
    1. 清除过期的差异动更包, 由运维定期清理
    2. QA提交申请, 删除整个版本号的目录, 删除后这个版本的客户端将不能进入游戏, 需要慎重

2015-07-28 Xiaoyu Created.
"""
from __future__ import print_function, with_statement

import sys
import time
import re
import os

from fabric.api import env, lcd, local, cd, run, put, execute, quiet, hosts, settings, hide

from bible.utils import set_fabric_common_env, TIMESTAMP
from bible.config_reader import ConfigReader

def version_tuple(v):
    return tuple(map(int, (v.split("."))))

def sorted_versions(versions, reverse=False):
    v_touples = [version_tuple(each) for each in versions]
    sorted_v_tuples = sorted(v_touples, reverse=reverse)
    return ['.'.join((str(v) for v in each)) for each in sorted_v_tuples]

def remote_file_exists(file):
    with quiet():
        return run('test -f "{}"'.format(file)).succeeded

def remote_dir_exists(file):
    with quiet():
        return run('test -d "{}"'.format(file)).succeeded

def remote_mkdir(dir):
    run('[[ -d {0} ]] || mkdir -p {0}'.format(dir))
    
def version_regex_check(version):
    if not re.match(r'[0-9]+(\.[0-9]+){3}', version):
        raise Exception("版本号:{} 不符合规则, 示例: 1.5.3.11".format(version))
 
def list_inner_scopes(root_dir, version):
    with cd('{}/{}'.format(root_dir, version)), hide('running', 'stdout'):
        result = run('''find ./ -mindepth 1 -maxdepth 1 -type d -print''')  
    return [each.lstrip('./') for each in result.splitlines()]

def list_existed_versions(root_dir):
    """
    列出前端目录下已经存在着的版本
    """
    with cd(root_dir), hide('running', 'stdout'):
        result = run('''( find ./ -mindepth 1 -maxdepth 1 -type d -print |grep --color=never -E '[0-9]+(\.[0-9]+){3}\\b' ) || echo "no_version_found"''')  

    if result == "no_version_found":
        return []
    else:
        return [each.lstrip('./') for each in result.splitlines()]

def list_existed_diff_packages(version_dir):
    with cd(version_dir), hide('running', 'stdout'):
        result = run('''( find ./ -mindepth 1 -maxdepth 1 -type f -print |grep --color=never -E '[0-9]+(\.[0-9]+){3}$' ) || echo "no_diff_package_found"''')  

    if result == "no_diff_package_found":
        return []
    else:
        return [each.lstrip('./') for each in result.splitlines()]

def list_platforms(root_dir):
    """
    列出前端目录下已经存在着的版本
    """
    def is_platform(dir):
        """
        通过判断version.lua是不是存在来判断这个目录是不是一个平台
        """
        with quiet():
            return run('test -f "{}/{}/version.lua"'.format(root_dir, dir)).succeeded

    with cd(root_dir), hide('stdout'):
        result = run('''find ./ -mindepth 1 -maxdepth 1 -type d -print |grep --color=never -vE '([0-9]+(\.[0-9]+){3}\\b)|(lyServers)' ''')  
    dirs = [each.lstrip('./') for each in result.splitlines()]

    return [each for each in dirs if is_platform(each)]

def filter_need_diff_versions(root_dir, start_zip_version, reverse=True):
    """
    筛选出需要做差异包的有哪些版本
    """
    existed_versions = list_existed_versions(root_dir)

    #start_zip_version版本之前的不做差异包
    if start_zip_version:
        _need_diff_versions = [each for each in existed_versions if version_tuple(each) >= version_tuple(start_zip_version)] 
    else:
        _need_diff_versions = existed_versions

    return sorted_versions(_need_diff_versions, reverse=reverse)

def platform_version(root_dir, platform):
    with cd(root_dir):
        result = run('grep sys_version.game {}/version.lua'.format(platform))
    return result.split('"')[1]

def delete_package(path_to_package):
    """
    删除指定动更差异包及其相关.lua文件
    """
    dir, filename = os.path.split(path_to_package)
    #文件名中不允许有空格存在
    if ' ' in filename:
        raise Exception("[ERROR] There is space in the filename: {}".format(path_to_package))
    filenames_to_delete = '{0} {0}.zip {0}.lua'.format(filename.replace('.zip', '')).split(' ')

    files = ['{}/{}'.format(dir, each) for each in filenames_to_delete]
    for each_file in files:
        print('Deleting if exists {}...'.format(each_file))
        with hide('running'):
            run('[[ ! -f "{0}" ]] || rm -f "{0}"'.format(each_file))

def clean_up_diff_packages(game, region):
    """
    清理动更差异包
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

    if conf.has_option("mobile_www_start_zip_version"):
        start_zip_version = conf.get("mobile_www_start_zip_version")
    else:
        start_zip_version = ""

    if conf.has_option("clean_30lv_diff_packages"):
        clean_30lv_diff_packages = conf.getboolean("clean_30lv_diff_packages")
    else:
        clean_30lv_diff_packages = False

    root_dir_prod = conf.get("mobile_www_root")
    root_dir_test = conf.get("mobile_www_root_test")

    @hosts(ip)
    def _do_clean_job(root_dir):
        need_scan_versions = filter_need_diff_versions(root_dir, start_zip_version, reverse=False)
        platforms = list_platforms(root_dir)

        _versions_in_use = []

        for each_platform in platforms:
            _version = platform_version(root_dir, each_platform)
            _versions_in_use.append(_version)

        versions_in_use = list(set(_versions_in_use))

        min_version = sorted_versions(versions_in_use)[0] #算出目前在用的最小的version

        for each_version_dir in need_scan_versions:
            _each_version_dir = "{}/{}".format(root_dir, each_version_dir)
            existed_diff_packages = sorted_versions(list_existed_diff_packages(_each_version_dir))

            #保留最近3个差异动更包
            for each_package in existed_diff_packages[0:-3]:
                #if version_tuple(each_package) < version_tuple(min_version):
                if each_package not in versions_in_use:
                    if clean_30lv_diff_packages: #目前只有gcmob需要清理30lv的差异包
                        _packages = '{0}/{1},{0}/{1}_preview,{0}/{1}_30lv'.format(_each_version_dir, each_package).split(',')
                    else:
                        _packages = '{0}/{1},{0}/{1}_preview'.format(_each_version_dir, each_package).split(',')

                    for each in _packages:
                        delete_package(each)

    #for each_root_dir in [root_dir_test]:
    for each_root_dir in [root_dir_test, root_dir_prod]:
        print('开始清理{}下的差异包...'.format(each_root_dir))
        execute(_do_clean_job, each_root_dir)

def main(args):
    if args.game and args.language and args.version:
        set_fabric_common_env()

        game = args.game
        region = args.language
        version = args.version.strip()
        #TODO
        print('Done!')

    elif args.game and args.language:
        set_fabric_common_env()

        game = args.game
        region = args.language

        clean_up_diff_packages(game, region)
        print('Done!')

    else:
        print('Use "-h" to see the command-line options')
        sys.exit(1)

def add_mobileWwwCleanUp_parser(parser):
    """
    添加参数和参数说明
    """
    sub_parser = parser.add_parser("mobileWwwCleanUp", help="手游前端资源清理")

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
        help="region, eg: cn, vn"
    )
    sub_parser.add_argument(
        '--clean',
        type=str,
        dest='clean_type',
        choices=['diff_packages', 'version_dirs'],
        help='select clean type'
    )
#    sub_parser.add_argument(
#        '--mode',
#        type=int,
#        dest='mode',
#        choices=[1, 2],
#        help='different game should have different mode'
#    )
    group = sub_parser.add_argument_group('more arguments when --clean version_dirs')
    group.add_argument(
        '-t',
        type=str,
        dest='version',
        help='mobile frontend version to delete, eg: 3.0.0.12,3.0.0.14,3.0.0.15'
    )
    sub_parser.set_defaults(func=main)
