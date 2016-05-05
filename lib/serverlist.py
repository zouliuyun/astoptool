#!/usr/bin/env python
#-*- coding:utf8 -*-
import json,os
import ssh,common,check

def filecheck(ip):
    dir = os.path.dirname(os.path.abspath(__file__))
    sshObj = getssh(ip)
    r1 = sshObj.cmd("test -f /app/opbin/allinone/serverlistOnServer.py && md5sum /app/opbin/allinone/serverlistOnServer.py|cut -d ' ' -f1")
    #print r1[1].strip(),common.calMd5(dir+"/serverlistOnServer.py")
    if r1[0] != 0 or r1[1].strip() != common.calMd5(dir+"/serverlistOnServer.py"):
        sshObj.cmd("[ ! -d /app/opbin/allinone/ ] && mkdir -p /app/opbin/allinone/")
        sshObj.put(dir + "/serverlistOnServer.py",remote_path="/app/opbin/allinone/",recursive=True)
def mycmd(ip,cmd):
    sshObj = getssh(ip)
    status,out,err = sshObj.cmd(cmd)
    if status!= 0:
        raise Exception(err)
    return out
def getssh(ip):
    import arg
    closegw = arg.gameOption("backstage_close_gw",type="bool",default=False)
    sshObj = ssh.ssh(ip,closegw=closegw)
    return sshObj
def getSingleMainServerList(backstageDB,headTag,partnersType,backstageIp):
    filecheck(backstageIp)
    servers = mycmd(ip=backstageIp,cmd="python /app/opbin/allinone/serverlistOnServer.py 'getSingleMainServerList' '%s' '%s' '%s'"%(backstageDB,headTag,partnersType))
    return json.loads(servers)
def getSingleMixServerList(backstageDB,headTag,partnersType,backstageIp):
    filecheck(backstageIp)
    servers = mycmd(ip=backstageIp,cmd="python /app/opbin/allinone/serverlistOnServer.py 'getSingleMixServerList' '%s' '%s' '%s'"%(backstageDB,headTag,partnersType))
    return json.loads(servers)
def getAllMainServerlist(backstageDB,headTag,partnersType,backstageIp):
    filecheck(backstageIp)
    servers = mycmd(ip=backstageIp,cmd="python /app/opbin/allinone/serverlistOnServer.py 'allMainServerlist' '%s' '%s' '%s'"%(backstageDB,headTag,partnersType))
    return json.loads(servers)
def getAllMixServerlist(backstageDB,headTag,partnersType,backstageIp):
    filecheck(backstageIp)
    servers = mycmd(ip=backstageIp,cmd="python /app/opbin/allinone/serverlistOnServer.py 'allMixServerlist' '%s' '%s' '%s'"%(backstageDB,headTag,partnersType))
    return json.loads(servers)
def getRecoverServerList(backstageDB,headTag,partnersType,backstageIp,serverName):
    if check.checkIp(serverName):
        ipType='ip'
    else:
        ipType='Name'
    filecheck(backstageIp)
    servers = mycmd(ip=backstageIp,cmd="python /app/opbin/allinone/serverlistOnServer.py 'getRecoverServer' '%s' '%s' '%s' '%s' '%s'"%(backstageDB,headTag,partnersType,ipType,serverName))
    return json.loads(servers)
def serverExists(backstageDB,headTag,partnersType,servername,backstageIp):
    filecheck(backstageIp)
    servers = mycmd(ip=backstageIp,cmd="python /app/opbin/allinone/serverlistOnServer.py 'serverExists' '%s' '%s' '%s' '%s'"%(backstageDB,headTag,partnersType,servername))
    return json.loads(servers)
def serverListExists(backstageDB,headTag,partnersType,servernameList,backstageIp):
    filecheck(backstageIp)
    servers = mycmd(ip=backstageIp,cmd="python /app/opbin/allinone/serverlistOnServer.py 'serverExists' '%s' '%s' '%s' '%s'"%(backstageDB,headTag,partnersType,servernameList))
    return json.loads(servers)
def serverRange(backstageDB,headTag,partnersType,type,backstageIp,startdate=None,enddate=None,serverlist=None,paichuserver=None):
    filecheck(backstageIp)
    servers = mycmd(ip=backstageIp,cmd="python /app/opbin/allinone/serverlistOnServer.py 'serverRange' '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s'"%(backstageDB,headTag,partnersType,type,startdate,enddate,serverlist,paichuserver))
    return json.loads(servers)
def serverInfo(backstageDB,headTag,partnersType,type,backstageIp,servername):
    filecheck(backstageIp)
    servers = mycmd(ip=backstageIp,cmd="python /app/opbin/allinone/serverlistOnServer.py 'serverInfo' '%s' '%s' '%s' '%s' '%s'"%(backstageDB,headTag,partnersType,type,servername))
    return json.loads(servers)
def getMixServer(backstageDB,headTag,partnersType,backstageIp,exclude):
    filecheck(backstageIp)
    return mycmd(ip=backstageIp,cmd="python /app/opbin/allinone/serverlistOnServer.py 'getMixServer' '%s' '%s' '%s' '%s'"%(backstageDB,headTag,partnersType,exclude))
if __name__ == "__main__":
    import state
    state.game = 'zjzr'
    state.language = 'cn_xianyu'
    #print getAllMainServerlist("acegi_gcmob",None,2,backstageIp="gcmob")
    #print getAllMixServerlist("acegi_gcmob",None,2,backstageIp="gcmob")
    #print serverExists("acegi_gcmob",None,2,"feiliu_1111",backstageIp="gcmob")
    #print serverRange("acegi_gcmob",None,2,"main",backstageIp="gcmob",startdate="2014-09-10")
    #print serverRange("acegi_gc",None , 1 ,"main", None, None, None, "10.6.197.229")
    print serverInfo("bs_zjzr",None,  2, "main", "123.59.76.159", "xianyu_2")
    #print getMixServer("acegi_gcmob",None,  2, "gcmob", "feiliu,mobile,feiliuapp")
    #a =  getSingleMixServerList("acegi_tjmob","大混服",  2, "tjmob")
    #print len(a),a
    #print getRecoverServerList("acegi_gc",None,  1,"gcld", '10.6.197.62')
    #print serverRange("acegi_gcmob",None,  2, "mix","10.6.197.36", None, None, "feiliu_.*")
    pass
