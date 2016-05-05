#!/usr/bin/env python
#-*- coding:utf8 -*-

from arg import *
import config,check,serverlist
import os
import ssh

class startup:
    def __init__(self,game,language,serverlist):
        self.game = game
        self.language = language
        self.serverlist = serverlist
    def run(type):
        if type != "stop" or type != "start" or type != "restart":
            print "执行的类型'%s'不允许！"%type
            sys.exit(1)
        uniqServers = thread.getUniqServer(self.serverlist)
        sshServers = thread.sshThread(uniqServers)
        r1 = thread.threadFunc(self.start,sshServers,gameServers,type=type)
    def start(sshObj,ip,servername,type):
        serverpath = "/app/%s_%s"%(self.game,servername)
        status,stdout,stderr = sshObj.cmd("test -d %s"%serverpath)
        if status != 0:
            print "[%s] 游戏目录%s不存在"%(servername,serverpath)
            return
        else:
            status,stdout,stderr = sshObj.cmd("export JAVA_HOME=/usr/local/jdk;export LC_ALL='en_US.UTF-8';export LANG='en_US.UTF-8';cd %s/backend/bin && sh startup.sh %s"%(serverpath,type))
            if status != 0:
                print "[%s] %s失败!\n%s\n%s"%(servername,type,stdout,stderr)
            else:
                print "[%s] %s"%(servername,stdout)
