#!/usr/bin/env python
#-*- coding:utf8 -*-
import sys,os

import state,ccthread
from arg import *

def execute(sshObj,ip,server,remotepath,localfile):
    cmdStr = remotepath.replace("${flag}",server).replace("${game}",state.game)
    msg = ""
    status = False
    try:
        sshObj.get(cmdStr,local_path=localfile)
        status = True
    except Exception,e1:
        msg = str(e1)
    outStr = "[\033[1;32;40m%s\033[0m] \033[1;34;40m[scp %s %s]\033[0m\n"%(server,cmdStr,localfile)
    if not status:
        outStr += "[\033[1;31;40mFail\033[0m]\n %s"%msg
        state.errorResult[server] = msg
    else:
        outStr += "[\033[1;32;40m下载成功!\033[0m]\n"
    outStr += "*" * 50 + "\n"
    print outStr
    sys.stdout.flush()
def get(localfile,remotefile):
    game = state.game
    language = state.language
    serverlist = getserverlist()
    state.servers = serverlist
    #state.servers = [["feiliu_10010","10.6.197.215"],["a","1.1.1.1"]]
    state.ignoreErrorHost = True
    ccthread.run(execute,remotefile,localfile)
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
        print "-------------更新失败服务器汇总为---------"
        print getSpecialServerIp(state.servers,state.errorResult.keys())
    print "----------------汇总-------------------"
    print "执行服务器总数: %d"%len(state.servers)
    print "执行失败服务器数: %d" %len(state.errorResult)
    print "连接失败IP数: %d" %len(state.errorHost)
    if not resultStatus:
        sys.exit(1)
