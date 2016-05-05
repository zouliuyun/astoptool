#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生产环境合服脚本。
请使用-h参数查看脚本帮助信息。

可以参照rundeck：
http://10.6.20.238/project/GCLD/job/show/6ec89e4f-0943-4b3a-9faf-a103a92ae168

2015-04-09 Xiaoyu Created Inital created.
"""
from fabric.api import env, local, run, execute, cd, quiet, hosts, parallel, lcd, settings, hide
import time, argparse, os, re, random, string
import sys

from bible.xiaoyu_utils import GameServer
from bible.utils import set_fabric_common_env, TIMESTAMP, RSYNC

from bible.arg import gameOption
from bible.uploader import Uploader
from bible.ftp import FTP as Ftp
from bible.backstage import Backstage

def mk_remote_dir(remote_dir):
    run(' mkdir -p {} '.format(remote_dir))

def tar_file(file):
    dir, filename = os.path.split(file)

    with cd(dir):
        run('tar zcvf {0}.tgz {0}'.format(filename))

def do_merge_on_target(s_server, t_server, source_server_sql, sequence):
    tmp_source_db = 'tmp_hf_{}_{}'.format(s_server, TIMESTAMP)

    with cd(REMOTE_DIR):
        run('tar zxvf {}.tgz'.format(source_server_sql))
        run('''pandora --update -e 'CREATE DATABASE {}' '''.format(tmp_source_db))
        run('''pandora --update {} <{}'''.format(tmp_source_db, source_server_sql))

    with cd('{}/merge_scripts'.format(REMOTE_DIR)):
        run("sed -i '/host:/c \    host: 127.0.0.1' db.yml")
        run("sed -i 's/db: db1/db: {}/' db.yml".format(t_server))
        run("sed -i 's/db: db2/db: {}/' db.yml".format(tmp_source_db))
        hfsql_path = '{}/hfsql'.format(REMOTE_DIR) #hf.py生成的一系列sql的存放路径
        mk_remote_dir(hfsql_path)
        run("sed -i '/output_path:/c output_path: {}/' db.yml".format(hfsql_path)) #注意最后一个/, 必须要有
        
        forceId1, forceId2, forceId3 = [int(each_id) for each_id in sequence.split('-')]

        run("sed -i -e 's/first_force_id/{}/' -e 's/second_force_id/{}/' -e 's/third_force_id/{}/' forceId.sql".format(forceId1, forceId2, forceId3))
        run('pandora --update {}<forceId.sql'.format(tmp_source_db))
        run('/usr/local/bin/python hf.py >hf.py.log')

    print('Importing hefu.sql to {}...'.format(t_server))
    sys.stdout.flush()
    with cd(hfsql_path):
        run('pandora --update {}<hefu.sql'.format(t_server))

    run('pandora --update -e "DROP DATABASE {}"'.format(tmp_source_db))

def parse_merge_list(file):
    from collections import OrderedDict

    if not os.path.isfile(file):
        print('File NOT exists: {}'.format(file))

    hf_list = local('''cat %s | awk 'BEGIN{pre=""}{$1="";if ($4 == "") $4=pre;else pre=$4;print "tjmob_"$2","$3",""tjmob_"$4}' ''' % (file), capture=True).splitlines()

    ret = OrderedDict()
    for each_group in hf_list:
        s_server, sequence, t_server = each_group.split(',')
        ret[t_server] = ret.get(t_server, [])
        ret[t_server].append((s_server, sequence))

    return ret

def check_local_merge_scripts(local_dir):
    scripts = ['clear_small_user.sql', 'db.yml', 'forceId.sql', 'hf.py', 'hf_reward.sql', 'table.yml']
    with settings(hide('everything')):
        with lcd(local_dir):
            for each_file in scripts:
                local('test -f {}'.format(each_file))

            for replace_str in ['first_force_id', 'second_force_id', 'third_force_id']:
                local('grep {} forceId.sql >/dev/null'.format(replace_str))

            local('grep "db: db1" db.yml')
            local('grep "db: db2" db.yml')


def single_merge(source_server, target_server, sequence, restart='no'):
    global REMOTE_DIR

    release_type = 'merge_{}_to_{}'.format(source_server, target_server)
    REMOTE_DIR = '/app/opbak/{}_{}'.format(release_type, TIMESTAMP)

    local_merge_scripts_dir = '/app/opbin/work/{}/merge_scripts/current'.format(source_server.game)
    print('Checking basic files for merge in the dir: {}...'.format(local_merge_scripts_dir))
    check_local_merge_scripts(local_merge_scripts_dir)

    print('Start merge {} to {}...'.format(source_server, target_server))

    for each_server in [source_server, target_server]:
        each_server.mkdir(REMOTE_DIR)
        local('{} {}/ {}:{}/merge_scripts/'.format(RSYNC, local_merge_scripts_dir, each_server.int_ip, REMOTE_DIR))

    #停服, 然后备份DB
    print('Stopping servers and dumping db...')
    for eachSrv in [source_server, target_server]:
        eachSrv.stop()
        eachSrv.dump_db(REMOTE_DIR)

    #合服之前对两个服都需要进行的sql
    _sqls_before_merge = ['clear_small_user.sql']
    sqls_before_merge = ['{}/merge_scripts/{}'.format(REMOTE_DIR, each) for each in _sqls_before_merge]

    for each_server in [source_server, target_server]:
        for each_sql in sqls_before_merge:
            each_server.sql_exec(each_sql)

    source_server_sql = source_server.dump_db(REMOTE_DIR, timestamp=time.strftime("%Y%m%d_%H%M%S"))
    
    execute(tar_file, source_server_sql, hosts=[source_server.int_ip])
    source_server_sql_tgz = '{}.tgz'.format(source_server_sql)

    #从被合服传输文件到保留服
    print('Transferring files from {} to {}:{}/ ...'.format(source_server.int_ip, target_server.int_ip, REMOTE_DIR))
    uploader1 = Uploader(source_ip=source_server.int_ip, target_ip=target_server.int_ip)
    uploader1.transfer([source_server_sql_tgz], REMOTE_DIR)

    #核心部分: DB合并
    print('Working on DB merge...')
    sys.stdout.flush()
    execute(do_merge_on_target, source_server, target_server, source_server_sql, sequence, hosts=[target_server.int_ip])

    if restart == 'yes':
        #导入全服补偿礼包并启动保留服
        hf_reward_sql = '{}/merge_scripts/hf_reward.sql'.format(REMOTE_DIR)
        print('Importing hf_reward.sql to {}...'.format(target_server))
        sys.stdout.flush()
        target_server.sql_exec(hf_reward_sql)
        print('Starting target server: {}'.format(target_server))
        target_server.start()

    #上传被合服日志到FTP
    print('Uploading logs to FTP...')
    #ftp1 = Ftp()
    #ftp1.upload_log(source_server.name)
    source_server.upload_log()

    #后台修改
    print('Modifing backstage info...')
    backstage = Backstage(source_server.game, region=REGION)
    ret_value = backstage.merge(s_server=source_server.name, t_server=target_server.name)
    if ret_value:
        print('[SUCC] Backstage merge info update.')
    else:
        print('[FAIL] Backstage merge  info update.')

    #手游入口修改
    print('Updating Mobile Entrance for {}...'.format(source_server))
    from bible.mobile_entrance import MobileEntrance
    mobile_entrance = MobileEntrance(source_server.game, REGION, source_server.yx, source_server.id)
    ret_value = mobile_entrance.merge(source_server.dns, target_server.dns, target_server.ext_ip, target_server.tcp_port)
    if ret_value:
        print('[SUCC] Mobile Entrance info update.')
    else:
        print('[FAIL] Mobile Entrance info update.')

    #移除被合服的相关目录, 文件和DB, 这个得放到最后, 前面的功能会有依赖
    print('Deleting source server {}...'.format(source_server))
    source_server.remove()

    print('Completed merge {} to {}.'.format(source_server, target_server))
    print('####################################################')

def bundle_merge(file):
    merge_details = parse_merge_list(file)
    print(merge_details)

    target_servers = merge_details.keys()
    print(target_servers)

    @parallel(pool_size=2) #控制同时并发合服的数量
    def _bundle_merge():
        target_server = GameServer(env.host_string)
        source_server_info_list = merge_details[target_server]
        for each_server, each_sequence in source_server_info_list[:-1]:
            each_source_server = GameServer(each_server)
            single_merge(each_source_server, target_server, each_sequence)

        #每一组合服中，最后一个被合服合完之后，全服发放合服礼包，并启动保留服。
        #比如: 依次将37wan_8,37wan_9,37wan_10合到37wan_7服，在37wan_10被合完之后，需要发放全服礼包，并重启37wan_7。
        last_source_server, last_sequence = source_server_info_list[-1]
        single_merge(last_source_server, target_server, last_sequence, restart='yes')

    execute(_bundle_merge, hosts=target_servers)

    print('Done!')

def main(args):
    global REGION

    set_fabric_common_env()
    game = args.game
    REGION = args.language

    if args.s_server and args.t_server and args.sequence and args.restart:
        sequence = args.sequence
        restart = args.restart

        s_server = '{}_{}'.format(game, args.s_server)
        t_server = '{}_{}'.format(game, args.t_server)

        source_server = GameServer(s_server)
        target_server = GameServer(t_server)

        single_merge(source_server, target_server, sequence, restart=restart)

        print('Done!')

    elif args.file:
        file = args.file
        bundle_merge(file)

    else:
        print('Use "-h" to see the command-line options')
        sys.exit(1)

def add_merge_parser(parser):
    """
    添加参数和参数说明
    """
    sub_parser = parser.add_parser("merge", help="合服")

    from add_argument import add_main

    add_main(sub_parser)

    sub_parser.add_argument(
        '-s',
        type=str,
        metavar='GameServer',
        dest='s_server',
        help='被合服, eg: 37wan_59'
    )
    sub_parser.add_argument(
        '-t',
        type=str,
        metavar='GameServer',
        dest='t_server',
        help='保留服, eg: 37wan_58'
    )
    sub_parser.add_argument(
        '-q',
        type=str,
        metavar='Sequence',
        dest='sequence',
        help='国家插入顺序, eg: 2-3-1'
    )
    sub_parser.add_argument(
        '-r',
        type=str,
        choices=['yes', 'no'],
        dest='restart',
        help='是否导入全服补偿并启动保留服, eg: no'
    )    
    sub_parser.add_argument(
        '-f',
        type=str,
        metavar='/PATH/TO/FILE',
        dest='file',
        help='指定批量合服列表的完整文件路径, eg: /app/opbin/work/tjmob/tmp/hf.list.20150508'
    )
    sub_parser.set_defaults(func=main)

