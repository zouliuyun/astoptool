#!/usr/bin/env python
#-*- coding:utf8 -*-

import os,sys
import state,ssh,arg,serverlist
import datetime
import ccthread

def cmd(myssh,cmdstr,servername):
    status,out,err = myssh.cmd(cmdstr)
    sys.stdout.write( "[%s]\n%s"%(cmdstr,out) )
    sys.stdout.flush()
    if status != 0:
        if servername not in state.errorResult:
             state.errorResult[servername] = ""
        state.errorResult[servername] += "[%s]\n%s"%(cmdstr,err)
        raise Exception(servername + ":" + err)
    return out

def executeSql(serverIpSshAstd,serverip,servername):
    sqlfile = state.game + "_" + servername + ".sql"
    remote_dir="/app/opbak/update/%s/allgamesql%s"%(curdate,curtime)
    cmd(serverIpSshAstd,"[ -d %s ] || mkdir -p %s"%(remote_dir,remote_dir),servername)
    try:
        serverIpSshAstd.put("%s"%sqlfile,remote_path="%s"%remote_dir)
    except Exception,e1:
        if servername not in state.errorResult:
             state.errorResult[servername] = ""
        state.errorResult[servername] += "put失败!"+str(e1)
        raise e1 

    db_name = "%s_%s"%(state.game,servername)
    backup = "%s_%s.sql"%(db_name,curtime)
    print "开始备份%s..."%db_name
    cmd(serverIpSshAstd,"/usr/bin/pandora --dump -R --opt %s > %s/%s"%(db_name,remote_dir,backup),servername)
    print "开始导入sql %s..."%sqlfile
    cmd(serverIpSshAstd,"/usr/bin/pandora --update %s < %s/%s"%(db_name,remote_dir,sqlfile),servername)
    print "%s执行sql %s完毕."%(db_name,sqlfile)
    os.system("rm -f %s"%sqlfile)
    try:
        os.system("sed -i '/ %s.sql/d' md5.txt"%db_name)
    except :
        pass

def arg_init(parser):
    parser.add_argument("-d",dest="sqldir",help="sql存放在ftp中sql目录中的目录名")

def run(options):
    global curdate,curtime,sqldir
    sqldir = options.sqldir.strip()
    state.ignoreErrorHost = True
    backstageDB = arg.gameOption("backstage_db")
    headTag = arg.gameOption("backstage_tag")
    is_mobile = arg.gameOption("is_mobile",type="bool")
    if is_mobile:
        partnersType = 2
    else:
        partnersType = 1
    backstageIp = arg.gameOption("backstage")
    #serverlistList = serverlist.serverRange(backstageDB,headTag,partnersType,"main",backstageIp,serverlist='.*')
    serverlistList = arg.getserverlist(ServerList=".*")
    #serverlistList = [["feiliu_88888",'10.6.196.30'],['feiliu_88889','10.6.196.30']]
    curdate = datetime.datetime.now().strftime("%Y%m%d")
    curtime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    ftpdir = "/app/online/%s/sql/%s/%s/"%(state.game,state.language,sqldir)
    if not os.path.isdir(ftpdir):
        print "%s不存在！"%ftpdir
        sys.exit(1)
    os.chdir(ftpdir)
    result=os.system("dos2unix md5.txt && chown virtual_user.virtual_user md5.txt && md5sum -c md5.txt")
    if result !=0:
        print "md5校验失败，请确认！"
        sys.exit(1)
    if os.path.exists( sqldir + ".zip"):
        status = os.system("unzip *.zip")
        if status != 0:
            print "解压%s.zip失败!"%sqldir
            sys.exit(1)
        else:
            if os.path.exists(sqldir):
                os.chdir(sqldir)
    newserverlist = []
    for file in os.listdir("."):
        if file.endswith(".sql"):
            servername = os.path.splitext(file)[0]
            for item in serverlistList:
                if state.game + "_" + item[0] == servername:
                    newserverlist.append(item)
                    break
            else:
                print "%s不存在该服务器列表"%servername
                state.errorResult[servername] = "不存在该服务器"
                continue
                #sys.exit(1)
    state.servers = newserverlist
    ccthread.run(executeSql)
    if len(state.errorHost) > 0:
        print "*" * 40,"连接失败ip如下:"
        print state.errorHost.keys()
    if len(state.errorResult) > 0:
        print "*"*40,"执行失败游戏服如下:"
        print arg.getSpecialServerIp(state.servers,state.errorResult.keys())
    print "执行游戏服数:",len(state.servers)
    print "执行失败数  :",len(state.errorResult)
    print "连接失败ip数:",len(state.errorHost)
    if len(state.errorResult) > 0 or len(state.errorHost) > 0:
        sys.exit(1)
