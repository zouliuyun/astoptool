#!/usr/bin/env python
#-*- coding:utf8 -*-

import ssh,state,common,backstage,serverlist,dns,getip
from arg import *
import paramiko
import os
import time,threading,Queue,datetime

def cmd(myssh,cmdstr):
    status,out,err = myssh.cmd(cmdstr)
    sys.stdout.write( "[%s]\n%s"%(cmdstr,out) )
    sys.stdout.flush()
    if status != 0:
        raise Exception(err)
    return out

def createBinlog():
    backstageIp = gameOption("backstage")
    backstageIpSsh = ssh.ssh(backstageIp,user="astd")
    backstageDb = gameOption("backstage_db")
    OUT = cmd(backstageIpSsh,"pandora %s -e 'select concat(server_flag,\"_\",replace(name,\"S\",\"\")) from server where n_ip = \"%s\" and server.status&1=1 and istest = 0 and server.mixflag = 1;'|grep -v 'concat(server_flag,'"%(backstageDb,failurIp))
    backstage_serverlist = OUT.split("\n")
    backstage_serverlist.remove('')
    print "backstage_serverlist:",backstage_serverlist
    diff = set(backstage_serverlist).difference(set(database_list))
    if len(diff) > 0:
        raise Exception("还原数据库包含后台不存在游戏服:%s"%str(diff))
    serverlist = " ".join(database_list)
    failurIpSsh.put("%s/../shell/copy_database.sh"%curdir,remote_path="/app")
    cmd(failurIpSsh,"sh /app/copy_database.sh '%s' '%s' '%s' '%s'"%(serverlist,state.game,backup_date,mysql_recover_dir))

def localRecover(db_name):
    cmd(failurIpSsh,"pandora --update -e 'drop database %s_%s'"%(state.game,db_name)) 
    cmd(failurIpSsh,"pandora --update -e 'create database %s_%s'"%(state.game,db_name))
    cmd(failurIpSsh,"pandora --update '%s_%s' < %s/%s/%s_%s.sql"%(state.game,db_name,mysql_recover_dir,recoverdate,state.game,db_name)) 

def recover(server,curssh,recoverSshAstd,ip):
    servername = state.game + "_" + server
    cmd(curssh,"test ! -d /app/%s"%servername)
    cmd(curssh,"rsync -av %s:/app/%s --exclude=logs --exclude=temp --exclude=fight /app/"%(failurIp,servername))
    logs = cmd(failurIpSsh,"find /app/%s -type f | grep %s"%(servername,nowdate))
    logsplit = logs.split("\n")
    logsplit.remove("")
    for line in logsplit:
        dir = os.path.dirname(line)
        cmd(recoverSshAstd,"mkdir -p %s"%dir)
        cmd(curssh,"rsync -av %s:%s %s"%(failurIp,line,line))
    cmd(recoverSshAstd,"cd /app/%s/backend && mkdir fight temp"%servername)
    cmd(curssh,"rsync -av %s:%s/%s/%s* /app/%s/"%(failurIp,mysql_recover_dir,backup_date,servername,servername))
    cmd(curssh,"/usr/bin/bzip2 -d /app/%s/%s_%s.sql.bz2"%(servername,servername,recoverdate))
    cmd(curssh,"pandora --update -e 'create database %s'"%servername)
    cmd(curssh,"pandora --update %s < /app/%s/%s_%s.sql"%(servername,servername,servername,recoverdate))
    cmd(curssh,"pandora --update %s < /app/%s/%s.binlog"%(servername,servername,servername))
    rwip = getip.getServerWip(ip)
    failurewip = getip.getServerWip(failurIp)
    if len(rwip) >0:
        print "%s:获取外网ip失败！"%ip
    else:
        newdianxinip = rwip[0]
        cmd(recoverSshAstd,"sed -i 's/%s/%s/g' /app/%s_*/www*/Config.xml"%(failurewip[0],rwip[0],servername))

def selectPort(server,ip,recoverIpSsh_Astd):
    servername = state.game + "_" + server
    allow_port = [8210,8220,8230,8240,8250,8260,8270,8280,8290,8300,8310,8320,8330,8340,8350,8360,8370,8380,8390]
    result = cmd(recoverIpSsh_Astd,"netstat -lntp | grep '^tcp'|awk '{print $4}' | awk -F':' '{print $NF}' | grep -v '^$' | sort -u")
    result = result.split('\n')
    result.remove('')
    for i in range(len(allow_port)):
        for j in allow_port:
            if str(allow_port[j]) in result:
                allow_port.remove(allow_port[j])

    tcp_port=cmd(recoverIpSsh_Astd,"grep 'port' /app/%s_%s/backend/apps/conf.xml | cut -d '>' -f2 | cut -d '<' -f1"%(state.game,servername))
    if str(tcp_port) in result:
        cmd(recoverIpSsh_Astd,"sed -i 's/%s/%s/g' /app/%s_%s/backend/apps/conf.xml"%(tcp_port,allow_port[0],state.game,servername))
        cmd(recoverIpSsh_Astd,"sed -i 's/%s/%s/g' /app/%s_%s/backend/apps/conf.xml"%(tcp_port,allow_port[0]+1,state.game,servername))

def changeBackstage(server,ip,recoverIpSsh_Astd):
    servername = state.game + "_" + server
    quhao = os.system("echo %s | awk -F '_' '{print $NF}'"%servername)
    yx_list = cmd(recoverIpSsh_Astd,"grep "gcld.yx =" /app/%s_%s/backend/apps/server.properties | awk -F '= ' '{print $NF}'"%(state.game,servername))
    yx_list = yx_list.split('\n')
    yx_list.remove('')
    for yx in yx_list:
        cmd(recoverIpSsh_Astd,"echo 'TOMCAT_PATH[%s_S%s]=/app/%s_%s/backend/' >> /app/%s_backstage/socket_gameserver.ini"%(%ys,quhao,state.game,servername,statge.game))
    cmd(recoverIpSsh_Astd,"sudo -u agent /app/%s_backstage/start.sh restart"%state.game)

def copyNginx(server,ip,recoverIpSsh):
    servername = state.game + "_" + server
    cmd(recoverIpSsh,"rsync -av %s:/app/nginx/conf/vhost/%s.conf /app/nginx/conf/vhost/"%(failurIp,servername))
    cmd(recoverIpSsh,"/app/nginx/sbin/nginx -t")
    cmd(recoverIpSsh,"/app/nginx/sbin/nginx -s reload")
def startService(server,recoverIpSsh_Astd):
    servername = state.game + "_" + server
    cmd(recoverIpSsh_Astd,"export JAVA_HOME=/usr/local/jdk;export LC_ALL='en_US.UTF-8';export LANG='en_US.UTF-8';sh /app/%s/backend/bin/startup.sh restart"%servername)

def stopGame(servername):
    pid = cmd(failurIpSshAstd,"ps x | grep 'java.*/app/%s_%s/' | grep -v grep | awk '{print $1}'"%(state.game,servername)).strip()
    if pid != "":
        cmd(failurIpSshAstd,"kill -9 %s"%pid)

def backstageChange(server,ip):
    wip = getip.getServerWip(ip)
    if len(wip) == 0:
        print "%s %s 获取外网失败！"%(server,ip)
        return 
    elif len(wip) == 1:
        dianxinIp = wip[0]
        liantongIp = dianxinIp
    else:
        dianxinIp = wip[0]
        liantongIp = wip[1]
    if int(allservers[server]["mixflag"]) == 1:
        data = {}
        data["servername"] = allservers[server]["servername"].replace("_","_S")
        data["n_ip"] = ip
        data["w_ip"] = dianxinIp
        data["cnc_ip"] = liantongIp
        backstageHeader = {"host":header}
        result = backstage.upBackstage(backstage_interface_url,data,backstageHeader)
        if result["status"]:
            print "%s 修改后台成功！"%server
        else:
            print "%s 修改后台失败！MSG：%s"%(server,result["msg"])
    pass

def executeDns(game,server,ip,level):
    result = dns.upDns(game,dnsgame,server,ip,level)
    if result["status"]:
        print "%s %s"%(server,result["msg"])
    else:
        print "ERROR:%s %s"%(server,result["msg"])

def dnsChange(server,ip):
    wips = getip.getServerWip(ip)
    for level in range(len(wips)):
        dnslevel = level + 1
        if ismobile:
            if allservers[server]["mixflag"] == 1:
                executeDns(state.game,server,wips[level],dnslevel)
        else:
            executeDns(state.game,server,wips[level],dnslevel)
def recoverByGame(servername,ip):
    stopGame(servername)
    if ip.strip() == failurIp.strip():
        localRecover(servername)
        startService(servername,failurIpSshAstd)
    else:
        recoverSsh = ssh.ssh(ip,user="root")
        recoverSshAstd = ssh.ssh(ip)
        recover(servername,recoverSsh,recoverSshAstd,ip)
        backstageChange(servername,ip) 
        dnsChange(servername,ip)
        copyNginx(servername,ip,recoverSsh)
        #selectPort(servername,ip,recoverSshAstd)
        startService(servername,recoverSshAstd)
        #changeBackstage(servername,ip,recoverSshAstd)

def recoverByMysql(failurIptemp,recoverDate,recoverfile):
    global recoverIpSsh,failurIpSsh,failurIpSshAstd,mysqldir,failurIp,curdir,recovermysqldir,backup_date,filename,recoverdate,nowdate,allservers,database_list,mysql_recover_dir,backstage_interface_url,header,ismobile,dnsgame
    dnsgame = gameOption("dns_game",state.game)
    backstage_interface_url = gameOption("backstage_interface_url")
    header = gameOption("backstage_header")
    backstageIp = gameOption("backstage")
    backstageIpSsh = ssh.ssh(backstageIp,user="astd")
    backstageDb = gameOption("backstage_db")
    headTag = gameOption("backstage_tag")
    ismobile = gameOption("is_mobile",type="bool")
    if ismobile:
        partnersType = 2
    else:
        partnersType = 1
    failurIp = failurIptemp
    curdir = os.path.abspath(os.path.dirname(__file__))
    filename = recoverfile
    f = open(filename).readlines()
    database_list = []
    for i in f:
        if i.strip() == "":
            continue
        i_split = i.split("@")
        database_list.append(i_split[0].strip())
    project = state.game
    backup_date = recoverDate
    mysql_recover_dir = "/app/opbak/mysqlrecover"
    recoverdate = datetime.datetime.strptime(backup_date,"%Y-%m-%d").strftime("%Y%m%d")
    nowdate = datetime.datetime.now().strftime("%Y-%m-%d")
    failurIpSsh = ssh.ssh(failurIp,user="root")
    failurIpSshAstd = ssh.ssh(failurIp)
    mysqldir = cmd(failurIpSsh,"grep '^innodb_data_home_dir' /etc/my.cnf | cut -d '=' -f 2|xargs echo").strip()
    #recovermysqldir = cmd(recoverIpSsh,"grep '^innodb_data_home_dir' /etc/my.cnf | cut -d '=' -f 2|xargs echo").strip()
    allservers = serverlist.getRecoverServerList(backstageDb,headTag,partnersType,backstageIp,failurIp)
    wip = getip.getServerWip(failurIp)
    if len(wip) >0 :
        olddianxinip = wip[0]
    else:
        raise Exception("获取外网ip失败！")
    #游戏还原
    createBinlog()
    threads = []
    for line in f:
        s = line.split("@")
        servername = s[0].strip()
        ip = s[1].strip()
        t = threading.Thread(target=recoverByGame,args=(servername,ip,))
        threads.append(t)
        t.start()
    for i in threads:
        i.join()
