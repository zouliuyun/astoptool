#!/usr/bin/env python
#coding=utf-8

import ssh,state,common,serverlist,backstage,dns,getip
from arg import *
import paramiko
import sys
import os
import datetime
import time

def cmd(myssh,cmdstr):
    status,out,err = myssh.cmd(cmdstr)
    sys.stdout.write( "[%s]\n%s"%(cmdstr,out) )
    sys.stdout.flush()
    if status != 0:
        raise Exception(err)
    return out
def logCopy():
    filename = '/app/remote_file.txt'
    cmd(failurIpSsh,'find /app/%s_* -name *.log > %s_temp'%(state.game,filename))
    cmd(failurIpSsh,'find /app/%s_* -name *.txt >> %s_temp'%(state.game,filename))
    cmd(failurIpSsh,"cat %s_temp | grep $(date +%%F) > %s"%(filename,filename))
    logfiles = cmd(failurIpSsh,"cat %s"%filename).split("\n")
    for log in logfiles:
        if log.strip() == "":
            continue
        dir = os.path.dirname(log)
        cmd(recoverIpSshAstd,"mkdir -p %s"%dir)
        cmd(failurIpSsh,"rsync -av %s %s:%s"%(log,recoverIp,dir))
def donwloadMysql():
    datestr = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    mysqlbackupDir = "/app/opbak/mysqlbackup/" + datestr
    cmd(recoverIpSsh,"mkdir -p %s"%mysqlbackupDir)
    cmd(recoverIpSsh,"mv %s/* %s/"%(recovermysqldir,mysqlbackupDir))
    cmdstr = "rsync -av %s/* --exclude=mysql-bin.* root@%s:%s/"%(mysqldir,recoverIp,recovermysqldir)
    cmd(failurIpSsh,cmdstr)
    failurIpSsh.put("%s/../shell/scp_binlog.sh"%curdir,remote_path="/app")
    cmd(failurIpSsh,"sh /app/scp_binlog.sh")
    try:
        cmd(failurIpSsh,'rsync -av /app/%s_backstage --exclude=log root@%s:/app'%(state.game,recoverIp))
    except Exception,e:
        print "WARNNING: scp /app/%s_backstage失败!ERR:%s"%(state.game,str(e))
def downloadNginx():
    cmd(failurIpSsh,"rsync -av /app/nginx/conf/vhost/* %s:/app/nginx/conf/vhost/"%recoverIp)
def download(data_file):
    cmdstr = "rsync -av /app/*%s* --exclude=log --exclude=logs root@%s:/app"%(data_file,recoverIp)
    cmd(failurIpSsh,cmdstr)

def change_configfile():
    oldWip = getip.getServerWip(failurIp)[0]
    recoverWip = getip.getServerWip(recoverIp)[0]
    cmd(recoverIpSshAstd,"sed -i 's/%s/%s/g' /app/%s_*/www*/Config.xml"%(oldWip,recoverWip,state.game))

def stop_service():
    try:
        cmd(recoverIpSsh,"service mysqld stop")
    except Exception,e1:
        print "WARNING：停止恢复服务器mysql报错!",str(e1)
    try:
        cmd(failurIpSsh,"service mysqld stop")
    except Exception,e2:
        print "WARNING：停止故障服务器mysql报错!",str(e2)
    pids = cmd(failurIpSshAstd,"ps x | grep '/usr/local/jdk/bin/java.*/app/%s_'|grep -v grep|awk '{print $1}'|xargs echo"%state.game).strip()
    if pids != "":
        cmd(failurIpSshAstd,"kill -9 %s"%pids)
def start_service():
    try:
        cmd(recoverIpSsh,"sudo -u agent /app/%s_backstage/start.sh restart"%state.game)
    except Exception,e1:
        print "WARNING: 启动/app/%s_backstage失败! ERR:%s"%(state.game,str(e1))
    cmd(recoverIpSsh,"service mysqld restart")
    cmd(recoverIpSshAstd,"sudo /app/nginx/sbin/nginx -s reload")
def startGame():
    gamedir = cmd(recoverIpSshAstd,"ls -d /app/%s*"%state.game)
    for game in gamedir.split("\n"):
        if game.strip() == "":
            continue
        try:
            cmd(recoverIpSshAstd,"export JAVA_HOME=/usr/local/jdk;export LC_ALL='en_US.UTF-8';export LANG='en_US.UTF-8';sh %s/backend/bin/startup.sh restart"%game)
        except Exception,e1:
            print "ERROR: %s 启动游戏失败!ERR:%s"%(game,str(e1))
def backstageChange():
    print allservers
    for server in allservers:
        print allservers[server]
        if int(allservers[server]["mixflag"]) == 1:
            data = {}
            data["servername"] = allservers[server]["servername"].replace("_","_S")
            data["n_ip"] = recoverIp
            data["w_ip"] = dianxinIp
            data["cnc_ip"] = liantongIp
            result = backstage.upBackstage(backstage_interface_url,data,header)
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
def dnsChange():
    for level in range(len(wips)):
        dnslevel = level + 1
        for server in allservers:
            if ismobile:
                if allservers[server]["mixflag"] == 1:
                    executeDns(state.game,server,wips[level],dnslevel)
            else:
                executeDns(state.game,server,wips[level],dnslevel)
def recoverByProject(failurIptemp,recoverIptemp):
    global recoverIpSsh,failurIpSsh,recoverIpSshAstd,mysqldir,failurIp,recoverIp,failurIpSshAstd,allservers,wips,ismobile,dianxinIp,liantongIp,header,backstage_interface_url,curdir,recovermysqldir,dnsgame
    dnsgame = gameOption("dns_game",default=state.game)
    failurIp = failurIptemp
    recoverIp = recoverIptemp
    curdir = os.path.abspath(os.path.dirname(__file__))
    project = state.game
    recoverIpSsh = ssh.ssh(recoverIp,user="root")
    failurIpSsh = ssh.ssh(failurIp,user="root")
    recoverIpSshAstd = ssh.ssh(recoverIp)
    failurIpSshAstd = ssh.ssh(failurIp)
    mysqldir = cmd(failurIpSsh,"grep '^innodb_data_home_dir' /etc/my.cnf | cut -d '=' -f 2|xargs echo").strip()
    recovermysqldir = cmd(recoverIpSsh,"grep '^innodb_data_home_dir' /etc/my.cnf | cut -d '=' -f 2|xargs echo").strip()
    stop_service()
    donwloadMysql()
    downloadNginx()
    download(state.game)
    logCopy()
    change_configfile()
    start_service()
    startGame()
    backstageDB = gameOption("backstage_db")
    headTag = gameOption("backstage_tag")
    ismobile = gameOption("is_mobile",type="bool")
    if ismobile:
        partnersType = 2
    else:
        partnersType = 1
    backstageIp =gameOption("backstage")
    header = {"host":gameOption("backstage_header")}
    backstage_interface_url = gameOption("backstage_interface_url")
    allservers = serverlist.getRecoverServerList(backstageDB,headTag,partnersType,backstageIp,failurIp)
    wips = getip.getServerWip(recoverIp)
    if len(wips) == 0:
        print "ERROR: 获取外网ip失败!"
    else:
        dianxinIp = wips[0]
        if len(wips) == 2:
            liantongIp = wips[1]
        else:
            liantongIp = wips[0]
    backstageChange()
    dnsChange()
    faileDirs = cmd(failurIpSshAstd,"find /app/ -maxdepth 1 -type d").split("\n")
    recoverDirs = cmd(recoverIpSshAstd,"find /app/ -maxdepth 1 -type d").split("\n")
    d1 = set(faileDirs).difference(set(recoverDirs))
    if len(d1) > 0:
        print "故障机器目录如下，请确认是否已完全迁移!"
        print d1
