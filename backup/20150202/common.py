#!/usr/bin/env python
#-*- coding:utf8 -*-
import re,sys,hashlib
import ssh,check
import traceback
import mysql,arg
def getServerWip(interIp):
    get_outip_from_zichan = arg.gameOption("get_outip_from_zichan",type="bool",default=False)
    iplist = []
    if not get_outip_from_zichan:
        sshobj = ssh.ssh(interIp.strip())
        cmd = "/sbin/ifconfig -a | grep 'inet addr'|cut -d':' -f2|cut -d' ' -f1"
        status,r,stderr = sshobj.cmd(cmd)
        if status == 0:
            for ip in r.split("\n"):
                if re.search(r"^(10\.|192\.168|172\.1[6-9]\.|172\.2[0-9]\.|172\.31\.|169\.254\.|127\.)",ip) or ip.strip() == "":
                    continue
                else:
                    iplist.append(ip.strip())
            if len(iplist) == 0:
                status,r1,stderr = sshobj.cmd("curl -s ip.cn | cut -d'：' -f2|cut -d' ' -f1")
                if check.checkIp(r1) :
                    iplist.append(r1.strip())
        else:
            print "[%s] out:%serr:%s"%(cmd,out,err)
    else:
        hsot = arg.mainOption("zichan_host")
        user = arg.mainOption("zichan_user")
        pwd = arg.mainOption("zichan_pwd")
        port = arg.mainOption("zichan_port",type="int")
        db = arg.mainOption("zichan_db")
        my = mysql.mysql(hsot,user,pwd,db,port)
        mylist = my.query("select asset_outip.ip,isp from asset_inip join asset_outip on asset_outip.did = asset_inip.did and asset_inip.ip = '%s'"%interIp)
        for i in mylist:
            if i[1].strip() == "电信":
                iplist.insert(0,i[0].strip())
            else:
                iplist.append(i[0].strip())
        pass
    return iplist
def exitError(strMsg):
    raise Exception(strMsg)
def systemCmd(cmd):
    status = os.system(cmd)
    if status != 0:
        exitError("ERROR:%s execute failed!"%cmd)
def calMd5(filepath):
    with open(filepath,'rb') as f:
        md5obj = hashlib.md5()
        md5obj.update(f.read())
        hash = md5obj.hexdigest()
        return hash
def statusCheck(status,stdout,stderr,msg=""):
    if status != 0:
        raise Exception("%s 执行失败!"%msg)
def urlopen(url,header=None,data=None):
    import urllib2,urllib
    try:
        dataencode = None
        if data:
            dataencode = urllib.urlencode(data)
        request = urllib2.Request(url,data=dataencode,headers=header)
        return 0,urllib2.urlopen(request).read()
    except Exception,e1:
        exstr = traceback.format_exc()
        return 1,exstr + "\n" + str(e1)
        
if __name__ == "__main__":
    import state
    state.game = "gcmob"
    state.language = "cn"
    print getServerWip("10.6.196.46")
    #print urlopen("http://192.168.202.6/backStage!addServer.action",header={"Host":"bs.nhmhw.aoshitang.com"},data={"name":"S100000","server_flag":"kabam","n_ip":"1.1.1.1","w_ip":"1.1.1.1","web_url":"1","cnc_ip":"1.1.1.1","startTime":"2011-10-10 10:00:00"})
