# -*- coding: utf-8 -*-
"""
生产环境部署新的match(要求用作模版的game_match_{id}必须存在并且可以从中控机ssh连接)，
请使用-h参数查看脚本帮助信息。

可以参照rundeck：
http://10.6.20.238/project/GCLD/job/show/6ec89e4f-0943-4b3a-9faf-a103a92ae168

2015-04-09 Xiaoyu Created Inital created.
"""

from fabric.api import env, lcd, local, run, execute, cd, quiet, hosts
from bible.uploader import Uploader
import time
import sys

TIME = time.strftime("%Y%m%d_%H%M%S")
RELEASE_TYPE = 'deploy_match'
REMOTE_DIR = '/app/opbak/{}_{}'.format(RELEASE_TYPE, TIME)

env.user = 'astd'
env.use_ssh_config = True   # This is important when running under root.
env.connection_attempts = 3
env.disable_known_hosts = True
env.keepalive = 60


def mk_remote_dir(remote_dir):
    run(' [ -d {0} ] || mkdir -p {0} '.format(remote_dir))

def template_matchServer_running(template_matchServer_ip, template_matchServer_id=1):
    
    template_matchServer = '{}_match_{}'.format(GAME, template_matchServer_id)

    @hosts(template_matchServer_ip)
    def _template_matchServer_running():
        with quiet():
            running = run('ps x | grep "[j]ava -Dstart.home=/app/{}/backend"'.format(template_matchServer)).succeeded
        if not running:
            raise Exception("Can't find the running java process for {}".format(template_matchServer))

    execute(_template_matchServer_running)

def remote_dir_exists(dir):
    with quiet():
        dir_exists = run('test -d {}'.format(dir)).succeeded
    return dir_exists

def matchServer_exists(matchServer, ip):
    with quiet():
        exists = local('''grep "\\b{}\\b" /etc/hosts '''.format(matchServer)).succeeded
    if exists:
        raise Exception('''The match server {} already exists in /etc/hosts'''.format(matchServer))
    else:
        matchServer_dir_exists = execute(remote_dir_exists, '/app/{}'.format(matchServer), hosts=[ip])[ip]
        if matchServer_dir_exists:
            raise Exception('''The match dir: /app/{} already exists on {}'''.format(matchServer, ip))

#def create_nginx_conf(remote_dir):
#    server_name = 'match_download_{}'.format(TIME)
#    conf_name = 'download_{}.conf'.format(TIME)
#    with cd('/app/nginx/conf/vhost'):
#        run('''echo -e "server {\\n    listen       80;\\n    server_name  %s;\\n    root %s;\\n    index Main.html;\\n    access_log  logs/default.access.log  main;\\n    location / {\\n        expires 0;\\n    }\\n\\n    error_page  404 500 502 503 504  /404.html;\\n}" >%s''' % (server_name, remote_dir, conf_name))

def reload_nginx():
    run('sudo /app/nginx/sbin/nginx -t')
    run('sudo /sbin/service nginx reload')

def packaging_data(matchServer, remote_dir):
    with cd('/app/{}'.format(matchServer)):
        run('tar zcf {}/matchServer.tgz * --exclude=backend/temp/* --exclude=backend/logs/*'.format(remote_dir))
    with cd(remote_dir):
        run('pandora --dump --opt -R -d {} >matchServer_init.sql'.format(matchServer))
        run('cp /app/nginx/conf/vhost/{}.conf ./nginx_matchServer.conf'.format(matchServer))
        run('tar zcf package.tgz *')

def fetch_and_inflat_package(template_matchServer_ip, remote_dir, matchServer):
    mk_remote_dir(remote_dir)
    with cd(remote_dir):
        #wget = 'wget -c -t 10 -T 10 -q'
        #server_name = 'match_download_{}'.format(TIME)
        #run('''{} --header="Host:{}" http://{}/package.tgz'''.format(wget, server_name, template_matchServer_ip))
        run('tar zxf package.tgz')
        with quiet():
            nginx_conf_exsits = run('test -f /app/nginx/conf/vhost/{}.conf'.format(matchServer)).succeeded
        if nginx_conf_exsits:
            run('mkdir backup')
            run('mv /app/nginx/conf/vhost/{}.conf backup/'.format(matchServer))
        run('cp nginx_matchServer.conf /app/nginx/conf/vhost/{}.conf'.format(matchServer))
        run('''pandora --update -e 'create database {}' '''.format(matchServer))
        run('''pandora --update {} <matchServer_init.sql'''.format(matchServer))
        run('''mkdir -p /app/{}'''.format(matchServer))
        run('''tar zxf matchServer.tgz -C /app/{}'''.format(matchServer))

def match_id_change(id):
    with cd('/app/{}_match_{}/backend/apps'.format(GAME, id)):
        #数据库配置文件修改
        run('''sed -ri '/name="driverUrl" value="jdbc:mysql:\/\/127.0.0.1:3306\//s/{0}_match_[0-9]{{1,3}}/{0}_match_{1}/' applicationContext.xml'''.format(GAME, id)) 
        #conf.xml修改
        run('''sed -ri '/name="ip" type="string"/s/match[0-9]{{1,3}}\\./match{}\\./' conf.xml'''.format(id))
        #server.properties修改
        run('''sed -i '/match.url *=/c match.url = match{}.{}.aoshitang.com:8092' server.properties'''.format(id, GAME))
        run('''sed -i '/match.name *=/c match.name = {}_match_{}' server.properties'''.format(GAME, id))

    with cd('/app/nginx/conf/vhost'):
        run('''sed -ri '/ *server_name +/s/match[0-9]{{1,3}}\\./match{0}\\./' {1}_match_{0}.conf'''.format(id, GAME))
        run('''sed -ri '/ *root +/s/match_[0-9]{{1,3}}/match_{0}/' {1}_match_{0}.conf'''.format(id, GAME))
        run('''sed -ri '/ *access_log +/s/match_[0-9]{{1,3}}/match_{0}/' {1}_match_{0}.conf'''.format(id, GAME))

def start_match_server(matchServer):
    run('set -m; /app/{}/backend/bin/startup.sh start && sleep 1'.format(matchServer))

class MatchServer(object):
    """
    MatchServer类，支持deploy操作。

    """
    def __init__(self, game, ip, id, template_matchServer_id, template_matchServer_ip, debug=False):
        global GAME

        if not debug: #控制是否输出debug详细信息
            from fabric.api import output
            output.everything = False

        GAME = game
        self.ip = ip
        self.id = id
        self.gw = '{}_gw'.format(GAME)
        self.dns = 'match{}.{}.aoshitang.com'.format(self.id, GAME)
        self.remote_dir = REMOTE_DIR

        self.template_matchServer_id = template_matchServer_id
        self.template_matchServer_ip = template_matchServer_ip
        self.template_matchServer = '{}_match_{}'.format(GAME, self.template_matchServer_id)

        self.matchServer = '{}_match_{}'.format(GAME, self.id)

        matchServer_exists(self.matchServer, ip)
        template_matchServer_running(self.template_matchServer_ip, self.template_matchServer_id)

    def job_on_template_server(self):
        
        @hosts(self.template_matchServer_ip)
        def _job_on_template_server():
            mk_remote_dir(self.remote_dir)
            print('正在以{}为模板制作压缩包，压缩包将生成在{}/package.tgz ...'.format(self.template_matchServer, self.remote_dir))
            packaging_data(self.template_matchServer, self.remote_dir)
            #print('正在搭建临时下载环境...')
            #create_nginx_conf(self.remote_dir)
            #reload_nginx()
            #ext_ip =  run('''curl -s ipip.net |awk '{split($2,x,"：");print x[2]}' ''')
            #return ext_ip
     
        #self.template_matchServer_ip = execute(_job_on_template_server)[self.template_matchServer]
        execute(_job_on_template_server)

    def job_on_target_server(self):
        
        @hosts(self.ip)
        def _job_on_target_server():
            #print('开始上载部署所需要的压缩包到{}:{},上载完毕后将自动解压...'.format(self.ip, self.remote_dir))
            fetch_and_inflat_package(self.template_matchServer_ip, self.remote_dir, self.matchServer)
            print('正在根据所需要的部署的match id，对模板内容进行更改...')
            match_id_change(self.id)
            reload_nginx()
            print('正在启动{}...'.format(self.matchServer))
            start_match_server(self.matchServer)

        execute(_job_on_target_server)

    def add_match_dns(self):
        
        @hosts('dns')
        def _add_match_dns(id, ip):
            dns_add_cmd = '/app/opbin/dns/dnsapi -g {0} -a add -d match{1}.{0} -l 1 -i {2}'.format(GAME, id, ip)
            print('用于添加域名解析的完整命令为: {}'.format(dns_add_cmd))
            ret_value = run(dns_add_cmd)
            if ret_value != 'Record add success':
                print('[WARNING] Failed to add dns, you can try again manually: {}'.format(dns_add_cmd)) 
        execute(_add_match_dns, self.id, self.ip)

#    def clean_job(self):
#
#        @hosts(self.template_matchServer)
#        def _clean_on_template_server():
#            with cd('/app/nginx/conf/vhost'):
#                run('rm -f download_{}.conf'.format(TIME))
#            reload_nginx() 
#
#        execute(_clean_on_template_server)

    def add_match_to_gw(self):
        
        @hosts('{}_gw'.format(GAME))
        def _add_match_to_gw():
            gw_db_name = '{}_gw'.format(GAME)
            mk_remote_dir(self.remote_dir)
            with cd(self.remote_dir):
                run('''pandora --dump --opt -R {0} match_server_info >{0}.match_server_info.sql.rb{1}'''.format(gw_db_name, TIME))
            run('''pandora --update {} -e 'INSERT INTO match_server_info (type,match_adress,match_id,match_name) VALUES (1,"{}:8092",{},"{}_match_{}");' '''.format(gw_db_name, self.dns, self.id, GAME, self.id))
            result = run('''pandora {} -e 'SELECT * FROM match_server_info' '''.format(gw_db_name))
            print('添加完毕。\n跨服GW中已登记的match信息:\n{}'.format(result))

        execute(_add_match_to_gw)

    def add_base_hosts_for_ssh(self):
        with lcd('/app/opbin/krb_hosts'):
            result = local('''grep -nE '[0-9]{1,3}(\.[0-9]{1,3}){3} +%s_match_%s' base_hosts''' % (GAME, self.id - 1))
            lines = result.splitlines()
            if len(lines) == 1:
                rowNum, line = lines[0].split(':', 1) #获取所在行行号
                run('cp base_hosts bak/base_hosts.rb{}'.format(TIME))
                run("sed -i '{}a {} {}' base_hosts".format(rowNum, self.ip, self.matchServer))
            else:
                print('[WARNING] Failed to add_base_hosts_for_ssh, can NOT locate a proper postion to add the new match entry, because there are more than one entry for {}_match_{}'.format(GAME, self.id - 1)) 

    def deploy(self):
        """
        部署
        """
        print('开始部署{}到IP为{}的目标主机上...'.format(self.matchServer, self.ip))
        sys.stdout.flush()
        self.job_on_template_server()
        print('部署需要的压缩包制作完毕。')

        print('正在上载压缩包到{}:{}/ ...'.format(self.ip, REMOTE_DIR))
        sys.stdout.flush()
        uploader1 = Uploader(source_ip=self.template_matchServer_ip, target_ip=self.ip)
        uploader1.transfer(['{}/package.tgz'.format(REMOTE_DIR)], REMOTE_DIR)

        print('开始解压压缩包...')
        self.job_on_target_server()
        print('启动{}完毕。'.format(self.matchServer))
        sys.stdout.flush()
        #print('开始摧毁{}上为传输文件临时搭建的下载环境...'.format(self.template_matchServer))
        #self.clean_job()
        #print('摧毁完毕。')
        print('正在为新的matchServer添加域名解析...')
        self.add_match_dns()
        print('正在将新的{}的信息添加到{}中的match_server_info表中...'.format(self.matchServer, self.gw))
        self.add_match_to_gw()
        print('正在添加{} {}到/app/opbin/krb_hosts/base_hosts'.format(self.ip, self.matchServer))
        self.add_base_hosts_for_ssh()

def deploy_matchServer(args):
    game = args.game
    ip = args.ip[0].replace(' ', '')
    id = args.id[0]
    template_matchServer_ip = args.template_ip[0].replace(' ', '')

    template_matchServer_id = args.template_id

    new_matchServer = MatchServer(game, ip, id, template_matchServer_id, template_matchServer_ip, debug=True)

    new_matchServer.deploy()
 

def add_deployMatch_parser(parser):
    """
    添加参数和参数说明
    """
    deployMatch_parser = parser.add_parser("deployMatch", help="部署新的match")

    deployMatch_parser.add_argument(
        "-g",
        "--game",
        dest="game",
        required=True,
        help="Game project name，eg: gcmob"
    )
    deployMatch_parser.add_argument(
        "-l",
        "--language",
        dest="language",
        required=True,
        help="Language，eg: cn, vn, ft"
    )
    deployMatch_parser.add_argument(
        '-t',
        type=str,
        nargs=1,
        required=True,
        metavar='IP',
        dest='ip',
        help='Internal Target IP, eg: 10.6.xx.xxx'
    )
    deployMatch_parser.add_argument(
        '-n',
        type=int,
        nargs=1,
        required=True,
        metavar='MATCH ID',
        dest='id',
        help='The match id you want to deploy, eg: 9'
    )
    deployMatch_parser.add_argument(
        '-p',
        type=str,
        nargs=1,
        required=True,
        metavar='IP',
        dest='template_ip',
        help='Internal Template match server IP, eg: 10.6.xx.xxx'
    )
    deployMatch_parser.add_argument(
        '-s',
        type=int,
        default=['1'],
        metavar='ID',
        dest='template_id',
        help='The template_match_id, eg: 1'
    )

    deployMatch_parser.set_defaults(func=deploy_matchServer)

