#!/usr/bin/env python
#-*- coding:utf8 -*-

import MySQLdb,json,re,datetime,sys

def conn(backstageDB,cmd):
    con = MySQLdb.connect(user='rd',passwd="qwert",host="127.0.0.1",db=backstageDB,charset="utf8")
    #con = MySQLdb.connect(user='rd',passwd="bJbT6uzB",host="127.0.0.1",db=backstageDB,charset="utf8")
    cursor = con.cursor()
    cursor.execute(cmd)
    return cursor.fetchall()
def nullCheck(arg):
    if arg == None or str(arg).lower() == "none" or str(arg).lower() == "null" or arg.strip() == "":
        return True
    else:
        return False
def getSingleMainServerList(backstageDB,headTag,partnersType):
    r1 = conn(backstageDB,'select concat(server.server_flag,"_",replace(server.name,"S","")),server.n_ip from server join partners on server.server_flag=partners.flag where server.status&1=1 and server.istest = 0 and server.mixflag = 1 and partners.status=1 and partners.name like "%s%%" group by server.server_flag'%headTag)
    serverList = []
    for i in r1:
        serverList.append([i[0],i[1]])
    return serverList
def getSingleMixServerList(backstageDB,headTag,partnersType):
    if nullCheck(headTag):
        header = ""
    else:
        header = ' and partners.name like "%s%%" '%headTag
    r1 = conn(backstageDB,'select concat(server.server_flag,"_",replace(server.name,"S","")),server.n_ip from server join partners on server.server_flag=partners.flag where server.status&1=1 and server.istest = 0 and partners.status=1 %s group by server.server_flag'%header)
    serverList = []
    for i in r1:
        serverList.append([i[0],i[1]])
    return serverList
def getAllMainServerlist(backstageDB,headTag,partnersType,startdate=None,enddate=None):
    whereStr = ""
    if not nullCheck(startdate):
        whereStr += ' and startTime >= "%s"' %startdate
    if not nullCheck(enddate):
        whereStr += ' and startTime <= "%s"' %enddate
    if not nullCheck(headTag):
        whereStr += ' and partners.name like "%s%%"' %headTag
    r1 = None
    #r1 = conn(backstageDB,'select concat(server.server_flag,"_",replace(server.name,"S","")), server.n_ip,startTime,web_url from server join partners on server.server_flag=partners.flag where server.status&1=1 and server.istest = 0 and server.mixflag = 1 and partners.type=%d and partners.status=1 %s'%(int(partnersType),whereStr))
    r1 = conn(backstageDB,'select concat(server.server_flag,"_",replace(server.name,"S","")), server.n_ip,startTime,web_url from server join partners on server.server_flag=partners.flag where server.status&1=1 and server.istest = 0 and server.mixflag = 1 and partners.status=1 %s'%whereStr)
    return r1
def getRecoverServerList(backstageDB,headTag,partnersType,ipType,serverName,serverlist=None):
    whereStr = ""
    if not nullCheck(headTag):
        whereStr += ' and partners.name like "%s%%"' %headTag
    r1 = None
    if ipType == "ip":
        whereStr += ' and server.n_ip="%s"' %serverName
    elif serverName.strip() != "":
        tmp=[]
        for s in serverName.replace("_","_S").split(","):
            tmp.append(s)
        for i in (range(len(tmp))):
            if i==0:
                whereStr += ' and (server.server_name="%s"' %tmp[i]
            else:
                whereStr += ' or server.server_name="%s"' %tmp[i]
        whereStr += ")"
        #whereStr += ' and server.server_name="%s"' %serverName.replace("_","_S")
    #r1 = conn(backstageDB,'select concat(server.server_flag,"_",replace(server.name,"S","")), replace(server_name,"S",""),startTime,web_url,server.mixflag from server join partners on server.server_flag=partners.flag where server.status&1=1 and server.istest = 0 and partners.type=%d and partners.status=1 %s'%(int(partnersType),whereStr))
    #r1 = conn(backstageDB,'select concat(server.server_flag,"_",replace(server.name,"S","")), replace(server_name,"S",""),startTime,server.mixflag from server join partners on server.server_flag=partners.flag where server.status&1=1 and server.istest = 0 and partners.type=%d and partners.status=1 %s'%(int(partnersType),whereStr))
    r1 = conn(backstageDB,'select concat(server.server_flag,"_",replace(server.name,"S","")), replace(server_name,"S",""),startTime,server.mixflag from server join partners on server.server_flag=partners.flag where server.status&1=1 and server.istest = 0 and partners.status=1 %s'%whereStr)
    #result = {"result":True}
    result = {}
    for server in r1:
        tempdict={}
        tempdict["servername"] = server[0]
        tempdict["MainName"] = server[1]
        tempdict["starttime"] = server[2].strftime("%Y-%m-%d %H:%M:%S")
        #tempdict["web_url"] = server[3]
        tempdict["mixflag"] = server[3]
        result[server[0]]=tempdict
    return result

def getAllMixServerlist(backstageDB,headTag,partnersType,startdate=None,enddate=None):
    whereStr = ""
    if not nullCheck(startdate):
        whereStr += ' and startTime >= "%s"' %startdate
    if not nullCheck(enddate):
        whereStr += ' and startTime <= "%s"' %enddate
    if not nullCheck(headTag):
        whereStr += ' and partners.name like "%s%%"' %headTag
    r1 = None
    #r1 = conn(backstageDB,'select concat(server.server_flag,"_",replace(server.name,"S","")), server.n_ip,startTime,web_url from server join partners on server.server_flag=partners.flag where server.status&1=1 and server.istest = 0 and partners.type=%d and partners.status=1 %s'%(int(partnersType),whereStr))
    r1 = conn(backstageDB,'select concat(server.server_flag,"_",replace(server.name,"S","")), server.n_ip,startTime,web_url from server join partners on server.server_flag=partners.flag where server.status&1=1 and server.istest = 0 and partners.status=1 %s'%whereStr)
    return r1
def serverExists(backstageDB,headTag,partnersType,servername):
    result = {"result":False}
    servers = getAllMixServerlist(backstageDB,headTag,partnersType)
    for row in servers:
        if row[0].strip() == servername.strip():
            result["result"] = True
            break
    return result
def serverListExists(backstageDB,headTag,partnersType,serverlist):
    result = {"result":False}
    servers = getAllMixServerlist(backstageDB,headTag,partnersType)
    for servername in serverlist.split(","):
        if servername.strip() == "":
            continue
        for row in servers:
            if row[0].strip() == servername.strip():
                result["result"] = True
                return result
                break
    return result
def serverRange(backstageDB,headTag,partnersType,type,startdate=None,enddate=None,serverlist=None,paichuserver=None):
    servers = ()
    if type == "mix":
        servers = getAllMixServerlist(backstageDB,headTag,partnersType,startdate,enddate)
    else:
        servers = getAllMainServerlist(backstageDB,headTag,partnersType,startdate,enddate)
    list = []
    for row in servers:
        if re.match(r'^%s$'%paichuserver,row[0]):
            continue
        if not re.match(r'^%s$'%serverlist,row[0]):
            continue
        list.append(row)
    return list
def serverInfo(backstageDB,headTag,partnersType,type,servername):
    result = {"result":True}
    sInfo = serverRange(backstageDB,headTag,partnersType,type,serverlist=servername)
    if len(sInfo) == 0:
        result["result"] = False
        result["msg"] = "get server info failed"
    elif len(sInfo) != 1:
        result["result"] = False
        result["msg"] = "get more than one server info"
    else:
        server = sInfo[0]
        result["servername"] = server[0]
        result["ip"] = server[1]
        result["starttime"] = server[2].strftime("%Y-%m-%d %H:%M:%S")
        result["web_url"] = server[3]
    return result    
def getMixServerList(backstageDB,headTag,partnersType,exclude):
    where = ""
    first = True
    haveWhere = False
    if exclude and exclude.strip() != "":
        for flag in exclude.split(","):
            if flag.strip() == "":
                continue
            haveWhere = True
            if first :
                where = " and flag not in ('%s'"%flag.strip()
            else:
                where += ",'%s'"%flag.strip()
            first = False
    if haveWhere:
        where += ")"
    if not nullCheck(headTag):
        #r1 = conn(backstageDB,'select flag from  partners where partners.name like "%s%%" and partners.type=%d and partners.status=1 %s'%(headTag,int(partnersType),where))
        r1 = conn(backstageDB,'select flag from  partners where partners.name like "%s%%" and partners.status=1 %s'%(headTag,where))
    else:
        #r1 = conn(backstageDB,'select flag from  partners where partners.type=%d and partners.status=1 %s'%(int(partnersType),where))
        r1 = conn(backstageDB,'select flag from  partners where partners.status=1 %s'%where)
    l = [i[0] for i in r1]
    return ",".join(l)
def toServerIp(list):
    result = []
    for row in list:
        result.append((row[0],row[1]))
    return result
if __name__ == "__main__":
    type = sys.argv[1]
    backstageDB = sys.argv[2]
    headTag = sys.argv[3]
    partnersType = sys.argv[4]
    if type == "allMainServerlist":
        print json.dumps(toServerIp(getAllMainServerlist(backstageDB,headTag,partnersType)))
    elif type == "allMixServerlist":
        print json.dumps(toServerIp(getAllMixServerlist(backstageDB,headTag,partnersType)))
    elif type == "serverExists":
        print json.dumps(serverExists(backstageDB,headTag,partnersType,sys.argv[5]))
    elif type == "serverListExists":
        print json.dumps(serverExists(backstageDB,headTag,partnersType,sys.argv[5]))
    elif type == "serverRange":
        print json.dumps(toServerIp(serverRange(backstageDB,headTag,partnersType,sys.argv[5],startdate=sys.argv[6],enddate=sys.argv[7],serverlist=sys.argv[8],paichuserver=sys.argv[9])))
    elif type == "serverInfo":
        print json.dumps(serverInfo(backstageDB,headTag,partnersType,sys.argv[5],sys.argv[6]))
    elif type == "getMixServer":
        print getMixServerList(backstageDB,headTag,partnersType,sys.argv[5])
    elif type == "getRecoverServer":
        print json.dumps(getRecoverServerList(backstageDB,headTag,partnersType,sys.argv[5],sys.argv[6]))
    elif type == "getSingleMainServerList":
        print json.dumps(getSingleMainServerList(backstageDB,headTag,partnersType))
    elif type == "getSingleMixServerList":
        print json.dumps(getSingleMixServerList(backstageDB,headTag,partnersType))

    #print getAllMixServerlist("acegi_gcmob","韩国",2)
    #print serverExists("acegi_gcmob","台湾",2,"coco_1")
    #print serverRange("acegi_gcmob","台湾",2,"mix",startdate="2014-08-10",enddate="2014-9-4")
    #print getRecoverServerList("acegi_gc","None",1,"","gcld_1,gcld_13",serverlist=None)
