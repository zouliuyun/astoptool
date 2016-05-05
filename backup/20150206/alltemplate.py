#!/usr/bin/env python
#-*- coding:utf8 -*-

from arg import *
import state,ssh,serverlist,template,ccthread
import threading,Queue

def errorAdd(servername,msg):
    if servername not in error:
        error[servername] = ""
    error[servername] += " %s "%msg
def put(servername,method):
    newserverTemplate = allTemplateObj[servername]
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
def mainServerTemplate(ip,servername,ismobile,type1):
    type = type1.split(",")
    for i in type:
        if i.strip() == "":
            continue
        if i.strip() in ["gametemplate","all"]:
            put(servername,"gametemplate")
        if i.strip() in ["www","all"] and ismobile:
            put(servername,"www")
    
def mixServerTemplate(ip,servername,ismobile,type1):
    type = type1.split(",")
    for i in type:
        if i.strip() == "":
            continue
        check = False
        if i.strip() in ["properties","all"]:
            put(servername,"properties")
        if i.strip() in ["www","all"] and not ismobile:
            put(servername,"www")
def getTemplateObj(ip,servername):
    try:
        t = template.template(state.game,state.language,servername,ip=ip)
        allTemplateObj[servername] = t
        #print ip,servername
    except Exception,e1:
        error[servername] = str(e1)
def mulutiProcess(serverlist,target,*args):
    queue = Queue.Queue()
    for i in serverlist:
        servername,ip = getServerIp(i)
        if queue.qsize() > 50:
            t1 = queue.get()
            t1.join()
        t = threading.Thread(target=target,args=(ip,servername).__add__(args))
        t.start()
        queue.put(t)
    for i in range(queue.qsize()):
        t1 = queue.get()
        t1.join()
def alltemplate(updatetype="all"):
    global allTemplateObj,error
    type = updatetype.split(",")
    error = {}
    allTemplateObj = {}
    backstageDB = gameOption("backstage_db")
    headTag = gameOption("backstage_tag")
    ismobile = gameOption("is_mobile",type='bool')
    if ismobile:
        partnersType = 2
    else:
        partnersType = 1
    backstageIp = gameOption("backstage")
    allMainServer = serverlist.getSingleMainServerList(backstageDB,headTag,partnersType,backstageIp)
    allMixServer = serverlist.getSingleMixServerList(backstageDB,headTag,partnersType,backstageIp)
    distinctServer = []
    mixUpdate,mainUpdate = False,False
    if ("gametemplate" in type or ("www" in type and ismobile) or "all" in type ) and ("properties" in type or ("www" in type and not ismobile) or "all" in type):
        mixUpdate,mainUpdate = True,True
        print "所有游戏服建立连接"
        for i in allMainServer + allMixServer:
            if i not in distinctServer:
                distinctServer.append(i)
    elif "gametemplate" in type or ("www" in type and ismobile) or "all" in type:
        mainUpdate = True
        print "所有主服建立连接"
        distinctServer = allMainServer
    elif "properties" in type or ("www" in type and not ismobile) or "all" in type:
        mixUpdate = True
        print "所有混服建立连接"
        distinctServer = allMixServer
    distinctServer.append(allMainServer[0])
    mulutiProcess(distinctServer,getTemplateObj)
    if mainUpdate:
        print "开始生成主服的游戏模板以及手游的www..."
        mulutiProcess(allMainServer,mainServerTemplate,ismobile,updatetype)
    if mixUpdate:
        print "开始生成混服的联运配置文件以及页游的www..."
        mulutiProcess(allMixServer,mixServerTemplate,ismobile,updatetype)
    print "开始生成通用模板..."
    commonServer = allMainServer[0][0]
    templateOjb = allTemplateObj[allMainServer[0][0]]
    for i in type:
        if i.strip() == "":
            continue
        if i.strip() in ["sql","all"]:
            put(commonServer,"sql")
        if i.strip() in ["common","all"]:
            put(commonServer,"common")
        if i.strip() in ["nginx","all"]:
            put(commonServer,"nginx")
    if len(error) > 0 :
        print "*"*50 + "初始化template对象失败:"
        for i in error:
            print "[%s] %s"%(i,error[i])
        raise Exception("更新模板失败!")
