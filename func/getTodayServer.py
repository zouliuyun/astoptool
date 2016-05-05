#!/usr/bin/env python
#-*- coding:utf8 -*-
'''
获取每日新开服版本信息

2015-09-26 Xiaoyun Created
'''
import time,sys,os,datetime

#from __future__ import print_function, with_statement

from fabric.api import env, lcd, local, cd, run, put, execute, quiet, hosts, settings, hide

from bible.utils import set_fabric_common_env, TIMESTAMP

from bible.config_reader import ConfigReader

from arg import gameOption, getserverlist

import mailhtml,sendmail

def null(Str):
    if Str == None or str(Str).lower().strip() == "none" or str(Str).strip() == "" or str(Str).lower().strip() == "null":
        Str=""
        return True
    else:
        return False

def gettodaylist(game, language):
    #d1 = datetime.date.today()
    d1 = datetime.date.today()
    d1 = d1 + datetime.timedelta(2)
    d2 = d1 + datetime.timedelta(4)
    serverList = []
    servers = {}
    result = local("python /app/opbin/work/bible/main.py  serverlist -g {} -l {} --startdate {} --enddate {} -s '.*'".format(game,language,d1,d2),capture=True)
    for i in result.split("\n"):
        serverList.append(i)
    nums = len(serverList)
    for i in serverList:
        server = i.split("@")[0]
        server_ip = i.split("@")[1]
        servers.setdefault(server_ip,[]).append(server)
    return servers,len

def exec_sql(game, language, backstage_db, backstageip, sql ):
    with settings(hide('running', 'stdout', 'stderr'),host_string=backstageip):
        return run('pandora -e "use {};{}"'.format(backstage_db,sql ))

def curl(dnsname):
    real_url = 'http://{}/root/gateway.action?command=version'.format(dnsname)
    return run('curl "{}"'.format(real_url))


def get_exec(game, language):
    conf = ConfigReader(game, language)
    if conf.has_option("gateway"):
        gateway = conf.get('gateway')
    else:
        gateway = ""
    backstage_db = conf.get('backstage_db')
    backstageip = conf.get('backstage')
    www_dir_type = conf.get('www_dir_type')
    email_address = conf.get('email_address')
    email_address = "zouly@game-reign.com"
    serverlist,nums = gettodaylist(game, language)
    html = mailhtml.mailhtml("%s_getTodayServer.html".format(game),"%s每日新开服(总开服数:%d)".format(game,nums)
    mail_title = "[%s]每日新开服列表".format(game)
    html.add("游戏服","后台时间","开服时间","清档时间","游戏前端版本","游戏后端版本","数据库版本")
    if len(serverlist) == 0:
        sys.exit(0)
    else:
        for server_ip in serverlist.keys():
            for server in serverlist[server_ip]:
                servername = game+"_"+server
                id = server.split("_")[1]
                yx = server.split("_")[0]
                sql= 'select startTime,mixflag from server where server_flag=\'{}\' and name=\'S{}\';'.format(yx,id)
                backstage_query = exec_sql(game, language, backstage_db, backstageip, sql)
                startTime,mixflag = local('echo "{}"|grep -vE "startTime|----"'.format(backstage_query),capture=True).strip('|').split('|')
                startTime = startTime.strip()
                cleartime = datetime.datetime.strptime(startTime,"%Y-%m-%d %H:%M:%S") - datetime.timedelta(minutes=30)
                opentime = datetime.datetime.strptime(startTime,"%Y-%m-%d %H:%M:%S") + datetime.timedelta(minutes=30)
                mixflag = mixflag.strip()
                if mixflag == 1:
                    Mainserver = game+"_"+server
                    if www_dir_type == "old":
                       www = "www"
                    else:
                       www = "www_"+server
                else:
                    sql = 'select concat(\'{}\',\'_\',server_name) as server from server where server_flag=\'{}\' and name=\'S{}\';'.format(game,yx,id)
                    backstage_query = exec_sql(game, language, backstage_db, backstageip, sql)
                    Mainserver = local('echo "{}"|grep -vE "server|----"'.format(backstage_query),capture=True).strip('|').replace('_S','_').strip()
                    www = "www_"+server
                if gateway == "":
                    with settings(host_string=server_ip):
                        cmd = 'pandora {}_{} -e \'select db_version from db_version\'|grep -v db_version'.format(game,server)
                        db_version = run(cmd)
                        cmd = 'grep -E "loadVersion.*http" /app/{}/{}/Main.html|sed /^$/d|head -1'.format(Mainserver,www)
                        www_version = run(cmd).split('/')[-2]
                        dnsname = run('grep server_name /app/nginx/conf/vhost/{}.conf'.format(Mainserver)).split(';')[0].split()[-1]
                        backend_version = curl(dnsname)
                else:
                    with settings(host_string=server_ip,gateway = gateway):
                        cmd = 'pandora {}_{} -e \'select db_version from db_version\'|grep -v db_version'.format(game,server)
                        db_version = run(cmd)
                        cmd = 'grep -E "loadVersion.*http" /app/{}/{}/Main.html|sed /^$/d|head -1'.format(Mainserver,www)
                        www_version = run(cmd).split('/')[-2]
                        dnsname = run('grep server_name /app/nginx/conf/vhost/{}.conf'.format(Mainserver)).split(';')[0].split()[-1]
                        backend_version = curl(dnsname)
                print servername,startTime,opentime,cleartime,www_version,backend_version,db_version
                html.add(servername,startTime,opentime,cleartime,www_version,backend_version,db_version)
    sendmail.sendmail(html.getCon(),email_address,mail_title,"NEWSERVER@game-reign.com")
def main(args):
    if args.game and args.language:

        game = args.game
        language = args.language
        get_exec(game, language)
        print('Done!')

    else:
        print('Use "-h" to see the command-line options')
        sys.exit(1)

def getTodayServer(parser):
    """
    添加参数和参数说明
    """
    sub_parser = parser.add_parser("getTodayServer", help="充值中控更新重启")

    sub_parser.add_argument(
        "-g",
        "--game",
        dest="game",
        required=True,
        help="game, eg: gcld"
    )
    sub_parser.add_argument(
        "-l",
        "--language",
        dest="language",
        required=True,
        help="language, eg: cn, vn"
    )

    sub_parser.set_defaults(func=main)
