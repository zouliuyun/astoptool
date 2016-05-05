#-*- coding:utf8 -*-

from fabric.api import run, quiet, local, execute, env
import time


from bible.config import Config
from bible.game import GameProject

def transform_gameservers(gameServers, all_server_info):
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

###############################################
#class GameServer
import time
import os
from fabric.api import env, local, run, execute, cd, quiet, with_settings, hosts

from bible.utils import TIMESTAMP


RELEASE_TYPE = 'temp_task'
REMOTE_DIR = '/app/opbak/{}_{}'.format(RELEASE_TYPE, TIMESTAMP)

def get_external_ip(int_ip):
    
    @hosts(int_ip)
    def _get_external_ip():
            ext_ip =  run('''curl -s ip.cn |awk '{split($2,x,"：");print x[2]}' ''')
            return ext_ip

    ret_value = execute(_get_external_ip)[int_ip]

    return ret_value

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
    def __init__(self, gameServer):
        self.name = gameServer
        self.game, self.yx, self.id = gameServer.split('_')
        self.master = '{}_{}'.format(self.yx, self.id) #主服名

        self._dns = None
        self._tcp_port = None
        self._ext_ip = None
        self._debug = True

        if not self._debug:
            #如果debug没开的话，关闭fabric的运行命令的输出
            from fabric.api import output
            output.everything = False

        gamePj = GameProject(self.game)
        
        self.int_ip = gamePj.all_gameServer_info[self.name]

    def __str__(self):
        return self.name
    
    def mkdir(self, remote_dir):

        @hosts(self.int_ip)
        def _mkdir():
            run(' [ -d {0} ] || mkdir -p {0} '.format(remote_dir))

        execute(_mkdir)

    @property
    def ext_ip(self):
        """
        The external ip for the game server. Will try to get only once and save to self._ext_ip for later use.
        """
        if not self._ext_ip:
            self._ext_ip = get_external_ip(self.int_ip)
        return self._ext_ip

    @property
    def tcp_port(self):
        """
        The tcp port used for the game server. Will try to get only once and save to self._tcp_port for later use.
        """

        def get_tcp_port():
            cmd = '''grep 'name="port" type="int"' conf.xml |awk -F[\<\>] '{print $3}' '''
    
            @hosts(self.int_ip)
            def _get_tcp_port():
                with cd('/app/{}/backend/apps'.format(self.name)):
                    result = run(cmd) 
    
                lines = result.splitlines()
                if len(lines) == 1:
                    return int(lines[0])
                else:
                    raise Exception("Can't get tcp port using cmd: {}".format(cmd))
    
            result = execute(_get_tcp_port)
            return result[self.int_ip]

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
    
            @hosts(self.int_ip)
            def _get_dns():
                with cd('/app/nginx/conf/vhost'.format(self.name)):
                    result = run(cmd)
    
                lines = result.splitlines()
                if len(lines) == 1:
                    return lines[0]
                else:
                    raise Exception("Can't get dns using cmd: {}".format(cmd))
    
            result = execute(_get_dns)
            return result[self.int_ip]

        if not self._dns:
            self._dns = get_dns()
        return self._dns

    def dump_db(self, remote_dir, timestamp=TIMESTAMP):
        
        dest = '{}/{}.sql.rb{}'.format(remote_dir, self.name, timestamp)
        self.mkdir(os.path.dirname(dest))

        @hosts(self.int_ip)
        def _dump_db():
            run('''pandora --dump --opt -R {} >{}'''.format(self.name, dest))
            return dest

        result = execute(_dump_db)

        return result[self.int_ip]

    def _operation(self, action):
        
        def _op():
            run('set -m; /app/{}/backend/bin/startup.sh {} && sleep 0.2'.format(self.name, action), warn_only=True)

        execute(_op, hosts=[self.int_ip])

    def stop(self):
        self._operation('stop')

    def start(self):
        self._operation('start')

    def restart(self):
        self._operation('restart')

    def sql_exec(self, sql_file):
        
        def _sql_exec():
            run('pandora --update {} <{}'.format(self.name, sql_file))

        execute(_sql_exec, hosts=[self.int_ip])

    def remove(self, remote_dir=None):
        """删除游戏服，以及游戏服上相关配置(nginx, backstage)"""
        
        if remote_dir is None:
            release_type = 'game_backup'
            remote_dir = '/app/opbak/{}_{}'.format(release_type, TIMESTAMP)

        self.stop()

        @hosts(self.int_ip)
        def _remove_game_server():
            mk_remote_dir(remote_dir)

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

        execute(_remove_game_server)

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
#End class GameServer
###############################################
