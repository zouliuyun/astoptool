#!/usr/bin/env python
#-*- coding:utf8 -*-

import ConfigParser,os
from common import *
import state,check
import re,serverlist

def getConfig(game):
    if check.nullCheck(game):
        raise Exception("请初始化game!")
    config = ConfigParser.ConfigParser()
    dir = os.path.dirname(os.path.abspath(__file__))
    path = "%s/../conf/" %dir
    filepath = path + game + ".conf"
    if not os.path.exists(filepath):
        raise Exception("ERROR: %s该配置文件不存在！"%game)
    config.read(filepath)
    return config
def checkArg(str,info):
    '''检查参数是否为空'''
    if check.nullCheck(str) :
        raise Exception(info)
def checkSection(config,section):
    '''检查配置文件的section是否存在'''
    if not config.has_section(section):
        raise Exception("没有%s该section"%section)
def getOption(config,language,option,type="str",default=None):
    '''检查配置文件的option是否存在'''
    if check.nullCheck(language):
        raise Exception("请初始化language!")
    checkSection(config,language)
    returnStr = ""
    if not config.has_option(language,option):
        #如果对应section中没有找到option则到通用的section中查找option
        if not config.has_option("common",option):
            if default != None:
                return default
            else:
                raise Exception("没有%s该option"%option)
            #return None
        else:
            if type == "bool":
                returnStr = config.getboolean("common",option)
            elif type == "int":
                returnStr = config.getint("common",option)
            elif type == "float":
                returnStr = config.getfloat("common",option)
            else:
                returnStr = config.get("common",option)
    else:
        if type == "bool":
            returnStr = config.getboolean(language,option)
        elif type == "int":
            returnStr = config.getint(language,option)
        elif type == "float":
            returnStr = config.getfloat(language,option)
        else:
            returnStr = config.get(language,option)
    #if re.match('.*_url',option) or option == 'title' or re.match(r'.*_url_tag',option):
    #    returnStr = returnStr.replace("${id}",quhao)
    return returnStr
def getMainConf():
    if state.mainconf != None:
        return state.mainconf
    mainconf = getConfig("main")
    state.mainconf = mainconf
    return mainconf
def getGameConf():
    if state.gameconf != None:
        return state.gameconf
    gameconf = getConfig(state.game)
    state.gameconf = gameconf
    return gameconf
def mainOption(option,type="str",default=None):
    return getOption(getMainConf(),"main",option,type,default)
def gameOption(option,type="str",default=None):
    return getOption(getGameConf(),state.language,option,type,default)
def getserverlist(ServerFile=None,ServerList=None,ExecludeServerList=None,StartDate=None,EndDate=None,UniqueServer=None):
    if ServerFile != None or ServerList != None or ExecludeServerList != None or StartDate != None or EndDate != None or UniqueServer != None:
        #print ServerFile,ServerList,ExecludeServerList,StartDate,EndDate,UniqueServer
        pass
    else:
        ServerFile = state.options.serverfile
        ServerList = state.options.serverlist
        ExecludeServerList = state.options.excludeServerlist
        StartDate = state.options.startdate
        EndDate = state.options.enddate
        UniqueServer = state.options.uniqserver
    slist = []
    if not check.nullCheck(ServerFile):
        for i in open(ServerFile).readlines():
            if i.strip() != "":
                if i.find("@") > 0:
                    s = i.split("@")
                    servername = s[0].strip()
                    ip = s[1].strip()
                else:
                    servername = i.strip()
                    if check.checkIp(i.strip()):
                        ip = i.strip()
                    else:
                        ip = state.game + "_" + i.strip()
                if not check.nullCheck( ServerList ):
                    if not re.match(r"^%s$"%ServerList,servername):
                        continue
                if not check.nullCheck(ExecludeServerList):
                    if re.match("^%s$"%ExecludeServerList,servername):
                        continue
                slist.append([servername,ip])
    else:
        if gameOption("is_mobile",type="bool"):
            partnersType = 2
        else:
            partnersType = 1
        slist = serverlist.serverRange(gameOption("backstage_db"),gameOption("backstage_tag"),partnersType,"main",gameOption("backstage"),StartDate,EndDate,ServerList,ExecludeServerList)
        #print StartDate,EndDate,ServerList,ExecludeServerList
        serverlist_tag = [ i.strip() for i in gameOption("serverlist_tag",default="").split(",") if i.strip() != "" ]
        for tag in serverlist_tag:
            slist += serverlist.serverRange(gameOption("backstage_db"), tag, partnersType,"main",gameOption("backstage"),StartDate,EndDate,ServerList,ExecludeServerList)
    if UniqueServer:
        return list(set(i[1].strip() for i in slist))
    else:
        return slist
def getYxNum(str):
    if not str:
        return [None,None]
    else:
        if not check.checkServer(str):
            return [None,None]
        else:
            return str.split("_")
def getServerIp(obj):
    if isinstance(obj,list):
        ip = obj[1]
        servername = obj[0]
    else:
        ip = obj
        servername = obj
    return servername,ip
def getKey(user,ip,port):
    return "%s@%s:%s"%(user,ip,str(port))
def splitKey(key):
    user,ipport = key.split("@",1)
    ip,port = ipport.split(":",1)
    return user,ip,port
def getSpecialServerIp(allserver,specailServerList):
    result = []
    try:
        for server in specailServerList:
            for item in allserver:
                if isinstance(item,list):
                    servername,ip = item[0],item[1]
                else:
                    servername,ip = item,item
                if servername == server:
                    result.append("%s@%s"%(servername,ip))
                    break
    except Exception,e1:
        result.append(str(e1))
    return "\n".join(result)
