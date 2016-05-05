#!/usr/bin/env python
#-*- coding:utf8 -*-
import sys,os

import state,ccthread
from arg import *

def execute(sshObj,ip,server,type):
    outStr = ""
    status,out,err = sshObj.cmd("test -d /app/%s_%s"%(state.game,server))
    if status != 0:
        state.errorResult[server] == "目录不存在"
    #sshObj.cmd("> /app/%s_%s/backend/logs/start.out"%(state.game,server))
    status,out,err = sshObj.cmd("export JAVA_HOME=/usr/local/jdk;export LC_ALL='en_US.UTF-8';export LANG='en_US.UTF-8';sh /app/%s_%s/backend/bin/startup.sh %s"%(state.game,server,type))
    if status != 0:
        state.errorResult[server] = "out:%s\nerr:%s"%(out,err)
        outStr += "[%s] Out:%s \nErr:%s"%(server,out,err)
    else:
        cmd = 'ps x -o stime,cmd|grep -v grep | grep -E "java.*%s_%s/"|awk \'{for(i=1;i<4;i++)printf ("%%s ",$i)}\''%(state.game,server)
        status,out,err = sshObj.cmd(cmd)
        outStr += "[%s] %s" %(server,out)
    print outStr
    sys.stdout.flush()
def restart(type):
    if not type:
        print "ERROR: restartType 必须指定!"
        sys.exit(1)
    game = state.game
    language = state.language
    serverlist = getserverlist()
    state.servers = serverlist
    #state.servers = [["feiliu_10010","10.6.197.215"],["a","1.1.1.1"]]
    state.ignoreErrorHost = True
    state.threadInterval = 3
    ccthread.run(execute,type)
    resultStatus = True
    if len(state.errorHost) > 0:
        print "-------------连接失败主机-----------------"
        print state.errorHost
        resultStatus = False
    if len(state.errorResult) > 0:
        resultStatus = False
        print "-------------命令执行失败服务器-----------"
        for i in state.errorResult:
            print "[%s] Error:%s"%(i,state.errorResult[i])
        print "-------------重启失败服务器汇总为---------"
        print getSpecialServerIp(state.servers,state.errorResult.keys())
    print "----------------汇总-------------------"
    print "执行服务器总数: %d"%len(state.servers)
    print "执行失败服务器数: %d" %len(state.errorResult)
    print "连接失败IP数: %d" %len(state.errorHost)
    if not resultStatus:
        raise Exception("重启失败!")
