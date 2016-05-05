# -*- coding: utf-8 -*-
'''
    手游前端强行使测试环境目录与正式环境同步


2015-09-02 Xiaoyu Created
'''

from __future__ import print_function, with_statement

from fabric.api import env, lcd, local, cd, run, put, execute, quiet, hosts, settings, hide

from bible.utils import set_fabric_common_env, TIMESTAMP
from bible.config_reader import ConfigReader

def sync(game, region):
    """
    强行使测试环境目录与正式环境同步
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

    root_dir_prod = conf.get("mobile_www_root")
    root_dir_test = conf.get("mobile_www_root_test")

    exclude_files = ['proxy.lua', 'lyServers']

    exclude_param = ' '.join(['--exclude={}'.format(each) for each in exclude_files])

    with settings(host_string=ip):
        run('''rsync -aqP --delete {exclude} {root_dir_prod}/ {root_dir_test}/'''.format(exclude=exclude_param, root_dir_prod=root_dir_prod, root_dir_test=root_dir_test))

def main(args):
    if args.game and args.language:
        set_fabric_common_env()

        game = args.game
        region = args.language
        sync(game, region)
        print('Done!')

    else:
        print('Use "-h" to see the command-line options')
        sys.exit(1)

def add_testEnvMobileWwwSync_parser(parser):
    """
    添加参数和参数说明
    """
    sub_parser = parser.add_parser("testEnvMobileWwwSync", help="手游前端资源使测试环境与正式环境完全同步")

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
    sub_parser.set_defaults(func=main)
