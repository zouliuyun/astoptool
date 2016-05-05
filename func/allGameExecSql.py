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
        raise Exception(err)
    return out

def executeSql(serverIpSshAstd,serverip,servername,sqlfile):
    remote_dir="/app/opbak/update/%s/allgamesql%s"%(curdate,curtime)
    cmd(serverIpSshAstd,"[ -d %s ] || mkdir -p %s"%(remote_dir,remote_dir),servername)
    try:
        serverIpSshAstd.put(sqlfile,remote_path="%s"%remote_dir)
    except Exception,e1:
        if servername not in state.errorResult:
             state.errorResult[servername] = ""
        state.errorResult[servername] += "put失败!"+str(e1)
        raise e1

    print "###################%s#######%s################"%(servername,sqlfile)
    db_name = "%s_%s"%(state.game,servername)
    backup = "%s_%s.sql"%(db_name,curtime)
    print "开始备份%s..."%db_name
    cmd(serverIpSshAstd,"/usr/bin/pandora --dump -R --opt %s > %s/%s"%(db_name,remote_dir,backup),servername)
    print "%s开始导入sql..."%db_name
    cmd(serverIpSshAstd,"/usr/bin/pandora --update %s < %s/%s"%(db_name,remote_dir,sqlfile),servername)
    print "%s执行sql完毕."%db_name

def arg_init(parser):
    parser.add_argument("--sqlfile",dest="sqlfile",help="sql存放在ftp sql目录中的路径")
def run(options):
    global curdate,curtime
    state.ignoreErrorHost = True
    serverlist = arg.getserverlist()
    #serverlist = [["feiliu_88888",'10.6.196.30'],['feiliu_88889','10.6.196.30']]
    state.servers = serverlist

    sqlfilepath = options.sqlfile.strip()
    sqldirpath = "/app/online/%s/sql/%s/%s"%(state.game,options.language,sqlfilepath)
    ftpdir = os.path.abspath(os.path.dirname(sqldirpath))
    sqlfile = os.path.basename(sqldirpath)
    if not ftpdir.startswith("/app/online/%s/sql/%s"%(state.game,state.language)):
        print "ftp path:%s路径错误!"%ftpdir

    curdate = datetime.datetime.now().strftime("%Y%m%d")
    curtime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    if not os.path.isdir(ftpdir):
        print "%s不存在！"%ftpdir
        sys.exit(1)
    os.chdir(ftpdir)
    result=os.system("dos2unix md5.txt && chown virtual_user.virtual_user md5.txt && md5sum -c md5.txt")
    if result !=0:
        print "md5校验失败，请确认！"
        sys.exit(1)
    ccthread.run(executeSql,sqlfile)
    if len(state.errorHost) > 0:
        print "*" * 40,"连接失败ip如下:"
        print state.errorHost.keys()
    if len(state.errorResult) > 0:
        print "*"*40,"执行失败游戏服如下:"
        print arg.getSpecialServerIp(state.servers,state.errorResult.keys())
    if len(state.errorHost) == 0 and len(state.errorResult) == 0:
        os.system("rm -f %s/%s"%(ftpdir,sqlfile))
    print "执行游戏服数:",len(state.servers)
    print "执行失败数  :",len(state.errorResult)
    print "连接失败ip数:",len(state.errorHost)
    if len(state.errorResult) > 0 or len(state.errorHost) > 0 :
        sys.exit(1)
