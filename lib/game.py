# -*- coding: utf-8 -*-
"""
基础的GameServer类，包含一些常见的操作

2015-04-17 Xiaoyu Created
"""
import time
import os
from fabric.api import env, local, run, execute, cd, quiet, with_settings, hosts, settings

from bible.utils import TIMESTAMP

from bible.arg import getserverlist
from bible import state

RELEASE_TYPE = 'temp_task'
REMOTE_DIR = '/app/opbak/{}_{}'.format(RELEASE_TYPE, TIMESTAMP)

def reload_nginx():
    run('sudo /app/nginx/sbin/nginx -t')
    run('sudo /sbin/service nginx reload')

def mk_remote_dir(remote_dir):
    run(' [ -d {0} ] || mkdir -p {0} '.format(remote_dir))

class GameServer(object):
    """
    The goal of this class is to module a typical game server and make the most common action for the game
    server to be easy to access.

    Don't Repeat Yourself.

    """
    def __init__(self, gameServer, ip=None):
        self.name = gameServer
        self.game, self.yx, self.id = gameServer.split('_')
        self.master = '{}_{}'.format(self.yx, self.id) #主服名

        self._dns = None
        self._tcp_port = None
        self._ext_ip = None
        self._debug = True

        #if not self._debug:
        #    #如果debug没开的话，关闭fabric的运行命令的输出
        #    from fabric.api import output
        #    output.everything = False

        if not ip:
            gamePj = GameProject(self.game)
        
            self.int_ip = gamePj.all_gameServer_info[self.name]

        else:
            self.int_ip = ip

    def __str__(self):
        return self.name
    
    def mkdir(self, remote_dir):
        with settings(host_string=self.int_ip):
            run(' [ -d {0} ] || mkdir -p {0} '.format(remote_dir))

    @property
    def ext_ip(self):
        """
        The external ip for the game server. Will try to get only once and save to self._ext_ip for later use.
        """
        if not self._ext_ip:
            with settings(host_string=self.int_ip):
                self._ext_ip =  run('''curl -s ip.cn |awk '{split($2,x,"：");print x[2]}' ''')
        return self._ext_ip

    @property
    def tcp_port(self):
        """
        The tcp port used for the game server. Will try to get only once and save to self._tcp_port for later use.
        """

        def get_tcp_port():
            cmd = '''grep 'name="port" type="int"' conf.xml |awk -F[\<\>] '{print $3}' '''

            with settings(host_string=self.int_ip), cd('/app/{}/backend/apps'.format(self.name)):
                result = run(cmd) 
    
            lines = result.splitlines()
            if len(lines) == 1:
                return int(lines[0])
            else:
                raise Exception("Can't get tcp port using cmd: {}".format(cmd))
    
        if not self._tcp_port:
            self._tcp_port = get_tcp_port()

        return self._tcp_port

    @property
    def dns(self):
        """
        The dns for the game server. Will try to get only once and save to self._dns for later use.
        """
        def get_dns():
            cmd = '''grep server_name %s.conf | awk '{print $2}' | tr -d ";" ''' % self.name

            with settings(host_string=self.int_ip), cd('/app/nginx/conf/vhost'.format(self.name)):
                result = run(cmd)
    
            lines = result.splitlines()
            if len(lines) == 1:
                return lines[0]
            else:
                raise Exception("Can't get dns using cmd: {}".format(cmd))

        if not self._dns:
            self._dns = get_dns()
        return self._dns

    def dump_db(self, remote_dir, timestamp=TIMESTAMP):
        
        dest = '{}/{}.sql.rb{}'.format(remote_dir, self.name, timestamp)
        self.mkdir(os.path.dirname(dest))

        with settings(host_string=self.int_ip): 
            run('''pandora --dump --opt -R {} >{}'''.format(self.name, dest))
        return dest

    def _operation(self, action):
        with settings(host_string=self.int_ip): 
            run('set -m; /app/{}/backend/bin/startup.sh {} && sleep 0.2'.format(self.name, action), warn_only=True)

    def stop(self):
        self._operation('stop')

    def start(self):
        self._operation('start')

    def restart(self):
        self._operation('restart')

    def sql_exec(self, sql_file):
        with settings(host_string=self.int_ip): 
            run('pandora --update {} <{}'.format(self.name, sql_file))

    def remove(self, remote_dir=None):
        """删除游戏服，以及游戏服上相关配置(nginx, backstage)"""
        
        if remote_dir is None:
            release_type = 'game_backup'
            remote_dir = '/app/opbak/{}_{}'.format(release_type, TIMESTAMP)

        self.stop()

        self.mkdir(remote_dir)

        with settings(host_string=self.int_ip): 
            with cd('/app'):
                run('mv {} {}/'.format(self.name, remote_dir))
            with cd(remote_dir):
                run('pandora --dump --opt -R {0}>{0}.sql.rb{1}'.format(self.name, TIMESTAMP))
                run('mv /app/nginx/conf/vhost/{}.conf ./'.format(self.name))

            reload_nginx()

            run('pandora --update -e "DROP DATABASE {}"'.format(self.name))

            with cd('/app/{}_backstage'.format(self.game)):
                run('cp socket_gameserver.ini {}/'.format(remote_dir))
                run("sudo -u agent sed -i '/\\b{}\\b/d' socket_gameserver.ini".format(self.name))
                run("set -m; sudo -u agent /bin/bash start.sh restart")

    def upload_log(self, logtype=None, date=None, logfile=None, ftp_ip=None):
        """
        :: Example
            pandora --ftp -r 30 -t 1200 -z -m 42.62.119.164 /tjmob_log/tjmob_37wan_1 /app/tjmob_37wan_1/backend/logs/game/dayreport/dayreport_2015-05-03.log.bz2*
        """
        from bible.utils import BZIP2

        ftp_log_path = '/{}_log/{}'.format(self.game, self.name)

        logtypes = ['dayreport', 'rtreport']

        date = date if date else time.strftime('%Y-%m-%d')
        ftp_ip = ftp_ip if ftp_ip else '42.62.119.164'

        if logfile:
            logfiles = [logfile]
        else:
            if logtype:
                logfiles = ['/app/{0}/backend/logs/game/{1}/{1}_{2}.log'.format(self.name, each_type, date) for each_type in logtype.split(',')]
            else:
                logfiles = ['/app/{0}/backend/logs/game/{1}/{1}_{2}.log'.format(self.name, each_logtype, date) for each_logtype in logtypes]

        for each_log in logfiles:
            dir, filename = os.path.split(each_log)
            file_bz2 = '{}.bz2'.format(filename)
            file_md5 = '{}.MD5'.format(file_bz2)
            with settings(host_string=self.int_ip), cd(dir): 
                run('[ -f {0} ] && echo "{0} already exists" || {1} {2}'.format(file_bz2, BZIP2, filename))
                run('[ -f {0} ] && echo "{0} already exists" || md5sum {1} >{0}'.format(file_md5, file_bz2))

            with settings(host_string=self.int_ip): 
                run('''pandora --ftp -r 30 -t 1200 -z -m {} {} {}.bz2*'''.format(ftp_ip, ftp_log_path, each_log) )

class GameProject(object):
    """
    GameProject 类，目前可以使用的是:
    1、获取所有游戏服信息;
    2、转换游戏服跟ip的对应关系，以使Fabric提高效率;

    后续功能添加中...
    """
    def __init__(self, game, region='cn'):
        self.game = game
        self.region = region
        self.all_gameServer_info = self._all_gameServer_info()
        self.all_gameserver_info = self.all_gameServer_info
        self.all_gameservers = self.all_gameServer_info.keys()

    def _all_gameServer_info(self):
        """
        Get all self.game info. It will get a dict like:
        
        { 'astd_17wan_1': '10.6.120.23', 
          'astd_37wan_98': '10.4.5.5',
                     .
                     .
                     .
          'astd_37wan_8': '10.4.5.15'}
   
        """
        #with quiet():
        #    result_info = local('''/app/opbin/work/global/getserverlist -g %s|awk -F@ -v OFS=@ '{print $1,$2}' ''' % self.game, capture=True)
        #info_list = result_info.splitlines()
        #info_dict = { each.split('@')[0]:each.split('@')[1] for each in info_list }

        with quiet():
            result_info = local('''/app/opbin/work/bible/main.py serverlist -g %s -l %s -s '.*' ''' % (self.game, self.region), capture=True)
        info_list = result_info.splitlines()

        info_dict = {}

        for each in info_list:
            name, ip = each.split('@')
            info_dict['{}_{}'.format(self.game, name)] = ip

        return info_dict
 
    def transform(self, gameServers, all_gameServer_info=None):
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
        if not all_gameServer_info:
            all_gameServer_info = self.all_gameServer_info

        IPS = list(set([ all_gameServer_info[each] for each in gameServers ]))
        locate_game_servers = { each:[] for each in IPS }
        for each in gameServers:
            locate_game_servers[all_gameServer_info[each]].append(each)
        return locate_game_servers
    
#    def sql_content_exec(self, gameServers, sql_content, backup='Yes', remote_dir=REMOTE_DIR):
#        locate_game_servers = self.transform(gameServers)
#        ips = locate_game_servers.keys()
#
#        def _sql_content_exec(sql_content, locate_game_servers, backup):
#            for gameServer in locate_game_servers[env.host_string]:
#                backup_dir = '{}/{}'.format(remote_dir, gameServer)
#                run('[ -d {0} ] || mkdir -p {0}'.format(backup_dir))
#                if backup.lower() == 'yes':
#                    run('pandora --dump --opt -R {0} >{1}/rollback_{0}.sql'.format(gameServer, backup_dir))
#                run('''pandora --update {} -e '{}' '''.format(gameServer, sql_content))
#
#        execute(_sql_content_exec, sql_content, locate_game_servers, backup=backup, hosts=ips)
#
    def upload_backend(self, version):
        local('''/app/opbin/rundeck/online.backend -t {} -g {}'''.format(version, self.game))
 
    def upload_log(self, logtype=None, date=None, logfile=None, ftp_ip=None):
        """
        An example: pandora --ftp -r 30 -t 1200 -z -m 42.62.119.164 /tjmob_log/tjmob_37wan_1 /app/tjmob_37wan_1/backend/logs/game/dayreport/dayreport_2015-05-03.log.bz2*
        """
        from bible.utils import BZIP2

        ftp_log_path = '/{}_log/{}'.format(self.game, self.name)

        logtypes = ['dayreport', 'rtreport']

        date = date if date else time.strftime('%Y-%m-%d')
        ftp_ip = ftp_ip if ftp_ip else '42.62.119.164'

        if logfile:
            logfiles = [logfile]
        else:
            if logtype:
                logfiles = ['/app/{0}/backend/logs/game/{1}/{1}_{2}.log'.format(self.name, logtype, date)]
            else:
                logfiles = ['/app/{0}/backend/logs/game/{1}/{1}_{2}.log'.format(self.name, each_logtype, date) for each_logtype in logtypes]

        @hosts(self.int_ip)
        def _upload_log():
            for each_log in logfiles:
                dir, filename = os.path.split(each_log)
                with cd(dir):
                    file_bz2 = '{}.bz2'.format(filename)
                    file_md5 = '{}.MD5'.format(file_bz2)
                    run('[ -f {0} ] && echo "{0} already exists" || {1} {2}'.format(file_bz2, BZIP2, filename))
                    run('[ -f {0} ] && echo "{0} already exists" || md5sum {1} >{0}'.format(file_md5, file_bz2))

                run('''pandora --ftp -r 30 -t 1200 -z -m {} {} {}.bz2*'''.format(ftp_ip, ftp_log_path, each_log) )

        execute(_upload_log)


#class Resource(object):
#    """
#    用来处理资源上传到中转临时资源服务器，或者从临时资源服务器下载。
#    每个项目的资源服务器可能各不相同。
#
#    """
#    def __init__(self, 
#
#    def upload(self, file):
#        dir, filename = os.path.split(file)
#        resource_dir = '/app/www/{}/{}/{}'.format(game, RELEASE_TYPE, TIMESTAMP) 
#        resource_ip = gameOption('www_ssh_ip')
#        execute(mk_remote_dir, resource_dir, hosts=[resource_ip])
#        local('rsync -aP {}/{{{},md5.txt}} {}:{}/'.format(dir, filename, resource_ip, resource_dir))
#    
#    def download(self, file):
#        remote_dir, filename = os.path.split(file)
#        mk_remote_dir(REMOTE_DIR)
#        with cd(remote_dir):
#            wget = 'wget -c -t 10 -T 10 -q'
#            server_name = gameOption('www_header')
#            for each_file in [filename, 'md5.txt']:
#                run('''{} --header="Host:{}" http://{}/{}/{}/{}/{}'''.format(wget, server_name, gameOption('www_ip'), game, RELEASE_TYPE, TIMESTAMP, each_file))
#            run('dos2unix md5.txt && md5sum -c md5.txt')
    
    
