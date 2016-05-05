#!/usr/bin/env python
#-*- coding:utf8 -*-

from arg import *
import state,ssh,serverlist,template,ccthread
import threading,Queue

def errorAdd(servername,msg):
    if servername not in error:
        error[servername] = ""
    error[servername] += " %s "%msg
def put(servername,ip,method):
    newserverTemplate = template.template(state.game,state.language,servername,ip=ip)
    check = False
    for i in range(10):
        try:
            if method.strip() == "sql":
                newserverTemplate.updateServerSql()
                check = True
            if method.strip() == "common":
                newserverTemplate.updateServerLib()
                check = True
            if method.strip() == "gametemplate":
                newserverTemplate.updateServerConf()
                check = True
            if method.strip() == "properties":
                newserverTemplate.updateServerProperties()
                check = True
            if method.strip() == "www":
                newserverTemplate.updateServerWww()
                check = True
            if method.strip() == "nginx":
                newserverTemplate.updateServerNginxConf()
                check = True
            break
        except:
            pass
    if not check:
        errorAdd(servername," %s模板生成失败! "%method)
def mainServerTemplate(ip,servername,big_mix_server,type1):
    type = type1.split(",")
    for i in type:
        if i.strip() == "":
            continue
        if i.strip() in ["gametemplate","all"]:
            put(servername,ip,"gametemplate")
        if i.strip() in ["www","all"] and big_mix_server:
            put(servername,ip,"www")
    
def mixServerTemplate(ip,servername,big_mix_server,type1):
    type = type1.split(",")
    for i in type:
        if i.strip() == "":
            continue
        check = False
        if i.strip() in ["properties","all"]:
            put(servername,ip,"properties")
        if i.strip() in ["www","all"] and not big_mix_server:
            put(servername,ip,"www")
def mulutiProcess(serverlist,method,big_mix_server,updatetype):
    queue = Queue.Queue()
    for servername,ip in serverlist:
        t = threading.Thread(target=method,args=(ip,servername,big_mix_server,updatetype))
        if queue.qsize() > state.threadingCount:
            t1 = queue.get()
            t1.join()
        queue.put(t)
        t.start()
    for i in range(queue.qsize()):
        t = queue.get()
        t.join()
def alltemplate(updatetype="all"):
    global error
    type = updatetype.split(",")
    error = {}
    big_mix_server = gameOption("big_mix_server",type="bool")
    backstageDB = gameOption("backstage_db")
    backstageIp = gameOption("backstage")
    is_mobile = gameOption("is_mobile",type="bool")
    headTag = gameOption("backstage_tag")
    if is_mobile:
        partnersType = 2
    else:
        partnersType = 1
    allMainServer = serverlist.getSingleMainServerList(backstageDB,headTag,partnersType,backstageIp)
    allMixServer = serverlist.getSingleMixServerList(backstageDB,headTag,partnersType,backstageIp)
    print "开始生成主服的游戏模板以及手游的www..."
    mulutiProcess(allMainServer,mainServerTemplate,big_mix_server,updatetype)
    print "开始生成混服的联运配置文件以及页游的www..."
    mulutiProcess(allMixServer,mixServerTemplate,big_mix_server,updatetype)
    print "开始生成通用模板..."
    servername,ip = allMainServer[0]
    for i in type:
        if i.strip() == "":
            continue
        if i.strip() in ["sql","all"]:
            put(servername,ip,"sql")
        if i.strip() in ["common","all"]:
            put(servername,ip,"common")
        if i.strip() in ["nginx","all"]:
            put(servername,ip,"nginx")
    if len(error) > 0 :
        print "*"*50 + "初始化template对象失败:"
        for i in error:
            print "[%s] %s"%(i,error[i])
        raise Exception("更新模板失败!")
