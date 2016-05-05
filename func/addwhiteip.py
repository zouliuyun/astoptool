#!/usr/bin/env python
#-*- coding:utf8 -*-

from arg import *
import check,ccthread,serverlist,state,common,ssh
import re

def updateProxy(sshobj,ip,server,iplist,yx,lyWhiteIpKey):
    filepath = "/app/%s_%s/backend/apps/%s.properties"%(state.game,server,yx)
    status,exists,err = sshobj.cmd("if [ -f %s ];then echo 1;else echo 0;fi"%filepath)
    if status != 0:
        state.errorResult[server] = "判断联运配置文件失败!%s"%err
        return 1
    if exists.strip() == "1":
        mainserver = state.game + "_" + server
        executeProperties(sshobj,ip,server,mainserver,iplist,yx,lyWhiteIpKey)

def updateProperties(sshobj,ip,server,iplist,yx,lyWhiteIpKey):
    status,mainserver1,err = sshobj.cmd("grep '\\[%s\\]' /app/%s_backstage/socket_gameserver.ini|cut -d '=' -f2|cut -d'/' -f3"%(server.replace("_","_S"),state.game))
    if status != 0:
        state.errorResult[server] = "获取主服失败"
        return 0
    else:
        mainserver = mainserver1.strip()
        executeProperties(sshobj,ip,server,mainserver,iplist,yx,lyWhiteIpKey)
def executeProperties(sshobj,ip,server,mainserver,iplist,yx,lyWhiteIpKey):
    cmdstr = "grep -E '^%s\\s*=' /app/%s/backend/apps/%s.properties"%(lyWhiteIpKey,mainserver,yx)
    #print cmdstr
    status,tempiplist1,err = sshobj.cmd(cmdstr)
    if status != 0:
        state.errorResult[server] = "[%s]获取联运白名单字段失败!err:%s"%(cmdstr,err)
        return 0
    else:
        tempiplist = tempiplist1.strip()
    if len(tempiplist.split("\n")) != 1:
        state.errorResult[server] = "获取联运白名单字段有冲突!获取的字段为:%s"%tempiplist
    elif tempiplist.find("=") < 0:
        state.errorResult[server] = "获取联运白名单配置字段失败!获取的字段为:%s"%tempiplist
    else:
        oldiplist = tempiplist.split("=")[1].strip()
        if oldiplist.find(";") >= 0:
            seprator = ";"
        else:
            seprator = ","
        if oldiplist == "":
            oldiplistList = []
        else:
            oldiplistList = [ i.strip() for i in oldiplist.split(seprator)]
        newIpList = iplist.split(",")
        newIpList += oldiplistList
        newiplistStr = seprator.join(list(set(newIpList)))
        cmdstr = "sed -i 's/\\(^%s\\s*=\\).*/\\1 %s/g' /app/%s/backend/apps/%s.properties"%(lyWhiteIpKey,newiplistStr,mainserver,yx)
        status,out,err = sshobj.cmd(cmdstr)
        if status != 0:
            state.errorResult[server] = "[%s] err:%s"%(cmdstr,err)
    pass
def addwhiteip(iplist,yx):
    if not check.checkIpList(iplist):
        raise Exception("iplist 格式不正确:%s"%iplist)
    backstageDB = gameOption("backstage_db")
    headTag = gameOption("backstage_tag")
    ismobile = gameOption("is_mobile",type='bool')
    lyWhiteIpKey = gameOption("lyWhiteIpKey")
    if ismobile:
        partnersType = 2
    else:
        partnersType = 1
    backstageIp = gameOption("backstage")
    mixservers = serverlist.serverRange(backstageDB,headTag,partnersType,"mix",backstageIp,serverlist="%s_.*"%yx)
    resultStatus = True
    if len(mixservers) == 0:
        raise Exception("没有获取到游戏列表，请确认!")
    state.servers = mixservers
    state.ignoreErrorHost = True
    ccthread.run(updateProperties,iplist,yx,lyWhiteIpKey)
    proxy_pay1_ip = gameOption("proxy_pay1_ip",default="")
    proxy_pay2_ip = gameOption("proxy_pay2_ip",default="")
    proxy_pay1 = gameOption("proxy_pay1",default="")
    proxy_pay2 = gameOption("proxy_pay2",default="")
    if proxy_pay1.strip() != "":
        proxy_pay1_ssh = ssh.ssh(proxy_pay1_ip)
        updateProxy(proxy_pay1_ssh,proxy_pay1_ip,proxy_pay1,iplist,yx,lyWhiteIpKey)
    if proxy_pay2.strip() != "":
        proxy_pay2_ssh = ssh.ssh(proxy_pay2_ip)
        updateProxy(proxy_pay2_ssh,proxy_pay2_ip,proxy_pay2,iplist,yx,lyWhiteIpKey)
    if len(state.errorResult) > 0:
        resultStatus = False
        print "\n","*" * 50
        for i  in state.errorResult:
            print "[%s] %s"%(i,state.errorResult[i])
    print "\n","*" * 50
    print "更新服务器数:%d"%len(mixservers)
    print "更新失败数:%d"%len(state.errorResult)
    print "连接失败服务器数量:%d"%len(state.errorHost)
    try:
        import template
        templateObj = template.template(state.game,state.language,mixservers[0][0],ip=mixservers[0][1])
        templateObj.updateServerProperties()
        print "更新模板成功!"
    except Exception,e1:
        resultStatus = False
        print "ERROR:模板更新失败!msg:%s"%str(e1)
    if not resultStatus:
        raise Exception("添加白名单失败!")
