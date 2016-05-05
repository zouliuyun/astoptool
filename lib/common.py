#!/usr/bin/env python
#-*- coding:utf8 -*-
import re,sys,hashlib,os,time
import traceback

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
        for i in range(10):
            try:
                return 0,urllib2.urlopen(request).read()
            except urllib2.URLError,e2:
                if str(e2).find("Connection timed out") >= 0 or str(e2).find("Connection reset by peer") >= 0:
                    print "WARNNING: 连接超时，1s后重试..."
                    time.sleep(1)
                    continue
                else:
                    raise e2
    except Exception,e1:
        exstr = traceback.format_exc()
        return 1,exstr + "\n" + str(e1)
        
if __name__ == "__main__":
    import state
    state.game = "gcmob"
    state.language = "cn"
    print getServerWip("10.6.196.46")
    #print urlopen("http://192.168.202.6/backStage!addServer.action",header={"Host":"bs.nhmhw.aoshitang.com"},data={"name":"S100000","server_flag":"kabam","n_ip":"1.1.1.1","w_ip":"1.1.1.1","web_url":"1","cnc_ip":"1.1.1.1","startTime":"2011-10-10 10:00:00"})
