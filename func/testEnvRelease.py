# -*- coding: utf-8 -*-
"""
线上测试服常规版本更新脚本(含前后端上传，更改前后端版本目录，sql执行，重启功能)，
请使用-h参数查看脚本帮助信息。

可以参照rundeck：
http://10.6.20.238/project/GCLD/job/show/ca6ba08a-760f-4a47-bed8-64b55ca88a68

2015-02-10 Xiaoyu Created
"""

from fabric.api import env, lcd, local, cd, run, execute, quiet, put
import time, argparse, os, re

from arg import gameOption

TIME = time.strftime("%Y%m%d_%H%M%S")

env.user = 'astd'
env.use_ssh_config = True   # This is important when running under root.
env.connection_attempts = 5
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
    info_dict = test_server_info()
    return info_dict

def test_server_info():
    _server_info = eval(gameOption('server_list'))

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
        pattern1 = '^%stest_[0-9]+(-[0-9]+){3}$' % GAME
        pattern2 = '^%stest_[a-z]{2,5}_[0-9]+(-[0-9]+){3}$' % GAME
        if re.match(pattern1, version):
            pass
        elif re.match(pattern2, version):
            return False
        else:
            raise Exception('Wrong version format: {}'.format(version))
    return True

def check_ftp_file(ftp_file):
    if ftp_file.lower() != 'no':
        file = "/app/online/{}/{}".format(GAME, ftp_file)
        if os.path.isfile(file):
            pass
        else:
            raise Exception('File NOT exists: {}'.format(file))

def versionTuple(v):
    return tuple(map(int, (v.split("."))))

def stop_gameServer(gameServer):
    run(''' set -m; /bin/bash /app/{}/backend/bin/startup.sh stop '''.format(gameServer), warn_only=True)

def start_gameServer(gameServer):
    run(''' set -m; /bin/bash /app/{}/backend/bin/startup.sh start '''.format(gameServer))

def upload_backend(version):
    local('''/app/opbin/rundeck/online.backend -t {} -g {}'''.format(version, GAME))

def upload_frontend(version):
    local('''/app/opbin/rundeck/online.frontend -t {} -g {}'''.format(version, GAME))

def update_backend(gameServer, version, mainland=True):
    backup_dir = '/app/opbak/{}/{}'.format(TIME, gameServer)
    run(''' [ -d {0} ] || mkdir -p {0} '''.format(backup_dir))
    with cd('/app/{}/backend/apps'.format(gameServer)):
        for conf_file in ['app.properties', 'plugins.xml']:
            #check if the config exists
            with quiet():
                conf_exists = run('test -f {}'.format(conf_file)).succeeded

            if conf_exists:
                run('cp {} {}/'.format(conf_file, backup_dir))
                if mainland:
                    cmd = ''' sed -i '/http:\/\/.*\/%s/s/%stest_[0-9]\{1,3\}-[0-9]\{1,3\}-[0-9]\{1,3\}/%s/g' %s ''' % (GAME, GAME, version, conf_file)
                else:
                    cmd = ''' sed -i '/http:\/\/.*\/%s/s/%stest_[a-z]\{2,5\}_[0-9]\{1,3\}-[0-9]\{1,3\}-[0-9]\{1,3\}/%s/g' %s ''' % (GAME, GAME, version, conf_file)
        
                run(cmd)

def update_frontend(gameServer, version, mainland=True): 
    """
    Mainland 用来区分是国内还是其他带有语种标示的后端目录，国内的后端目录类似tjmob_3-8-9-9，其他地区的后端目录类似tjmob_tw_3-9-9-9.
    """
    game, yx, id = gameServer.split('_')
    backup_dir = '/app/opbak/{}/{}'.format(TIME, gameServer)
    run('[ -d {0} ] || mkdir -p {0}'.format(backup_dir))
    with cd('/app/{}/www_{}_{}'.format(gameServer, yx, id)):
        run(' cp Main.html {}/Main.html_{} '.format(backup_dir, gameServer))
        if mainland:
            cmd = ''' sed -i '/http:\/\/cdn.*\.aoshitang.com\/%stest_/s/%stest_[0-9]\{1,3\}-[0-9]\{1,3\}-[0-9]\{1,3\}/%s/g' Main.html ''' % (GAME, GAME, version)
        else:
            cmd = ''' sed -i '/http:\/\/cdn.*\.aoshitang.com\/%stest_/s/%stest_[a-z]\{2,5\}_[0-9]\{1,3\}-[0-9]\{1,3\}-[0-9]\{1,3\}/%s/g' Main.html ''' % (GAME, GAME, version)

        run(cmd)

def sql_exec(gameServer, sql_file):
    sql_filename = sql_file.split('/')[-1]
    backup_dir = '/app/opbak/{}'.format(TIME)
    run('[ -d {0} ] || mkdir -p {0}'.format(backup_dir))
    with cd(backup_dir):
        run(''' pandora --dump --opt -R {0} >{0}.sql.rb{1} '''.format(gameServer, TIME))
        run(''' pandora --update {} <{} '''.format(gameServer, sql_filename))

# These are Fabric tasks below
def transfer(file):
    from bible.utils import RSYNC
    file_dir, filename = os.path.split(file)
    remote_dir = '''/app/opbak/{}'''.format(TIME)
    run(''' [ -d {0} ] || mkdir -p {0} '''.format(remote_dir))

    #cmd = ''' {rsync} {file_dir}/{{{filename},md5.txt}} {ssh_user}@{target_host}:{remote_dir}/ '''.format(file_dir=file_dir, target_host=env.host_string, remote_dir=remote_dir, ssh_user=env.user, filename=filename, rsync=RSYNC)
    #local(cmd)
    with lcd(file_dir):
        put(filename, remote_dir)
        put('md5.txt', remote_dir)

    with cd(remote_dir):
        run('dos2unix md5.txt && md5sum -c md5.txt')

def upload(fVer_4, bVer_4, fUpload, bUpload):
    if fVer_4.lower() != 'no' and fUpload == 'Yes':
        print('Start upload frontend...')
        upload_frontend(fVer_4)
    if bVer_4.lower() != 'no' and bUpload == 'Yes':
        print('Start upload backtend...')
        upload_backend(bVer_4)

def update(fVersion, bVersion, sql_file, maindland, restart='No'):
    if sql_file.lower() != '/app/online/{}/no'.format(GAME):
        transfer(sql_file)
    for gameServer in LOCATE_GAME_SRVS[env.host_string]:
        if restart in ['Yes', 'Restart', 'Stop']:
            stop_gameServer(gameServer)
        if bVersion.lower() != 'no':
            update_backend(gameServer, bVersion, maindland)
        if fVersion.lower() != 'no':
            update_frontend(gameServer, fVersion, maindland)
        if sql_file.lower() != '/app/online/{}/no'.format(GAME):
            sql_exec(gameServer, sql_file)
        if restart in ['Yes', 'Restart', 'Start']:
            start_gameServer(gameServer)


class Release(object):
    """
    Note
    """
    def __init__(self, args):
        if args.filename and args.gameServers and args.frontendVersion and args.backendVersion and args.gateway:
            global GAME, IPS, LOCATE_GAME_SRVS, GAME_SRVS
            GAME = args.game
            self.ftp_file = args.filename[0].replace(' ', '').strip('/')
            self.gameServers = args.gameServers[0].replace(' ', '')
            self.fVer_4 = args.frontendVersion[0].replace(' ', '')
            self.bVer_4 = args.backendVersion[0].replace(' ', '')
            self.restart = args.restart[0]
            self.fUpload = args.fUpload[0]
            self.bUpload = args.bUpload[0]

            gateway = args.gateway

            if gateway != 'No':
                env.gateway = gateway

            #Check arguments value
            f_mainland = check_end_version(self.fVer_4)
            b_mainland = check_end_version(self.bVer_4)

            if self.fVer_4.lower() != 'no' and self.bVer_4.lower() != 'no':
                if f_mainland == b_mainland:
                    self.mainland = f_mainland
                else:
                    raise Exception('The front and backend version are NOT matched, they should be in same region.')
            else:
                self.mainland = f_mainland and b_mainland

            check_ftp_file(self.ftp_file)


            self.sql_file = "/app/online/{}/{}".format(GAME, self.ftp_file)
            
            self.fVer = '-'.join(self.fVer_4.split('-')[0:3])
            self.bVer = '-'.join(self.bVer_4.split('-')[0:3])

            GAME_SRVS = ['{}_{}'.format(GAME, each) for each in self.gameServers.split(',')]
            check_game_servers(GAME_SRVS)

            LOCATE_GAME_SRVS = transform_gameServers(GAME_SRVS)
            IPS = LOCATE_GAME_SRVS.keys()

    def run(self):
            print('Game Servers below will be updated: {}'.format(GAME_SRVS))

            upload(self.fVer_4, self.bVer_4, self.fUpload, self.bUpload)
            execute(update, self.fVer, self.bVer, self.sql_file, self.mainland, restart=self.restart, hosts=IPS)

            print('Done!')

def add_args_for_testEnvRelease(parser):
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
        '-f',
        type=str,
        default=['No'],
        nargs=1,
        metavar='/PATH/TO/FILE',
        dest='filename',
        help='The SQL file that with full FTP PATH, eg: /update/sql/2014-09/01/xxx.sql'
    )
    parser.add_argument(
        '--gateway',
        type=str,
        default='No',
        dest='gateway',
        help='gateway for ssh connection, eg: ast_hk'
    )
    parser.add_argument(
        '-t',
        type=str,
        nargs=1,
        metavar='GameServers',
        dest='gameServers',
        help='Game Servers, eg: game_yaowan_58,game_37wan_8'
    )
    parser.add_argument(
        '-r',
        type=str,
        choices=['Yes', 'No', 'Stop', 'Start', 'Restart'],
        default=['No'],
        nargs=1,
        metavar='Yes/No',
        dest='restart',
        help='Need resart?, eg: Yes/No'
    )
    parser.add_argument(
        '--f-upload',
        type=str,
        choices=['Yes', 'No'],
        default=['No'],
        nargs=1,
        metavar='Yes/No',
        dest='fUpload',
        help='Frontend Upload?, eg: Yes/No'
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
        '-a',
        '--front-version',
        type=str,
        default=['No'],
        nargs=1,
        metavar='Frontend Version',
        dest='frontendVersion',
        help='Frontend Version, eg: gametest_2-4-50-0'
    )
    parser.add_argument(
        '-b',
        '--backend-version',
        type=str,
        default=['No'],
        nargs=1,
        metavar='Backend Version',
        dest='backendVersion',
        help='Backend Version, eg: gametest_2-4-50-0'
    )
 
