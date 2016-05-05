#!/usr/bin/env python
#-*- coding:utf8 -*-
import sys,os,time
import commands

import state,ccthread,ssh,check
from arg import *

def cmd(sshobj,server,cmd):
    status,out,err = sshobj.cmd(cmd)
    #print "[%s] out:%s"%(cmd,out)
    if status != 0:
        errorDict[server] = "[%s] error:%s"%(cmd,err)
        raise Exception("[%s] [%s] err:%s"%(server,cmd,err))
    return out
def keywordCheck(sshObj,updateType,keyword,logfile):
    time.sleep(2)
    hotswapResult = None
    for key in keyword.split(","):
        key = key.strip()
        if key == "":
            continue
        if updateType == "update":
            status,stdout,err = sshObj.cmd('grep -i -E -A 50 "reload.*%s" %s | grep "reload succ"'%(key,logfile))
        else:
            status,stdout,err = sshObj.cmd('grep -i -E -A 50 "%s" %s | grep "remote succ"'%(key,logfile))
        if status == 0:
            hotswapResult = True
        else:
            hotswapResult = False
            break
    return hotswapResult
def execute(sshObj,ip,server,type,keyword,www_ip,www_port,www_header):
    print "开始动更%s ..."%server
    sys.stdout.flush()
    status,pid,err = sshObj.cmd("ps x | grep '/usr/local/jdk/bin/java.*\<%s_%s\>' | grep -v 'grep' | awk '{print $1}'"%(state.game,server))
    status,direxists,err = sshObj.cmd("if [ -d /app/%s_%s ];then echo 1;else echo 0;fi")
    if pid.strip() == "" :
        if direxists.strip() == "1":
            errorDict[server] = "获取游戏pid失败"
            sys.stdout.write(server + "获取游戏pid失败")
            return
        elif  direxists.strip() == "0": #没有pid并且没有目录，则说明是混服
            errorDict[server] = "没有pid并且没有目录"
            sys.stdout.write(server + "没有pid并且没有目录")
            return
        elif direxists.strip() == "":
            sys.stdout.write(server + "判断是否有游戏目录失败")
            errorDict[server] = "判断是否有游戏目录失败"
            return
    status,log,err = sshObj.cmd("if [ -f /app/%s_%s/backend/logs/start.out ];then echo 1; elif [ -f /app/%s_%s/logs/start.out ];then echo 2;else echo 0;fi"%(state.game,server,state.game,server))
    if status != 0 :
        sys.stdout.write(server + "日志文件获取失败")
        errorDict[server] = "日志文件获取失败"
        return
    elif log.strip() == "1":
        logfile = "/app/%s_%s/backend/logs/start.out"%(state.game,server)
    elif log.strip() == "2":
        logfile = "/app/%s_%s/logs/start.out"%(state.game,server)
    else:
        sys.stdout.write(server + "日志文件获取失败")
        errorDict[server] = "日志文件获取失败"
        return 
    workdir = "/app/opbin/%s/allinone/hotswap/%s"%(state.game,server)
    cmd(sshObj,server,"rm -rf %s && mkdir -p %s"%(workdir,workdir))
    wgetStr = "wget -c -t 10 -T 10 --header='HOST:%s' http://%s:%s/%s/hotswap/hotswap.zip" %(www_header,www_ip,www_port,state.game)
    cmd(sshObj,server,"cd %s && %s"%(workdir,wgetStr))
    cmd(sshObj,server,"> %s"%logfile)
    cmd(sshObj,server,"cd %s && unzip -q -o hotswap.zip && cd hotswap && chmod +x attach remote update"%workdir)
    if type == "update":
        updateLog = cmd(sshObj,server,"cd %s/hotswap && ./update %s" %(workdir,pid.strip()))
    else:
        updateLog = cmd(sshObj,server,"cd %s/hotswap && ./remote %s" %(workdir,pid.strip()))
    if not keywordCheck(sshObj,type,keyword,logfile):
        sys.stdout.write("[%s]\n%s\n获取关键字失败\n"%(server,updateLog))
        errorDict[server] = "关键字获取失败"
    else:
        succList.append(server)
    sys.stdout.flush()
def hotswap(type,keyword,backendVersion=None):
    global succList,errorDict
    succList = []
    errorDict = {}
    game = state.game
    language = state.language
    www_ip = gameOption("www_ip")
    www_ssh_ip = gameOption("www_ssh_ip")
    www_port = gameOption("www_port",default="80")
    www_header = gameOption("www_header")
    www_root = gameOption("www_root")
    www_ssh = ssh.ssh(www_ssh_ip)
    www_hotswap_dir = "%s/%s/hotswap"%(www_root,game)
    www_ssh.cmd("mkdir -p " + www_hotswap_dir)
    if type != "update" and type != "remote":
        print "ERROR: 动更类型必须为update或者remote!"
        sys.exit(1)
    www_ssh.put("/app/online/%s/hotswap/%s/hotswap.zip"%(game,language),remote_path=www_hotswap_dir)
    ##动更包上传资源目录后删除ftp上的动更包
    os.popen("rm -f /app/online/%s/hotswap/%s/hotswap.zip"%(game,language))
    serverlist = getserverlist()
    state.servers = serverlist
    #state.servers = [["feiliu_10010","10.6.197.215"]]
    state.ignoreErrorHost = True
    ccthread.run(execute,type,keyword,www_ip,www_port,www_header)
    resultStatus = True
    if len(state.errorHost) > 0:
        print "-"*40 + "连接失败主机" + "-"*30
        print state.errorHost
        resultStatus = False
    if len(errorDict) > 0:
        print "-"*40 + "命令执行失败服务器" + "-"*24
        for i in errorDict:
            print "[%s] Error:%s"%(i,errorDict[i])
        print "-"*40 + "更新失败服务器汇总为" + "-"*22
        print getSpecialServerIp(state.servers,errorDict.keys())
        resultStatus = False
    print "-"*40 + "汇总" + "-"*38
    print "更新服务器总数: %d"%len(state.servers)
    print "更新失败服务器数: %d" %len(errorDict)
    print "更新成功服务器数: %d" %len(succList)
    sys.stdout.flush()
    if not check.nullCheck(backendVersion):
        print "*" * 40 + "开始上传后端..."
        status,out = commands.getstatusoutput("sh /app/opbin/rundeck/online.backend -t '%s' -g '%s'"%(backendVersion,game))
        print out
        if status != 0:
            print "ERROR: 后端%s上传失败!"%backendVersion
            resultStatus = False
    if not resultStatus:
        sys.exit(1)

