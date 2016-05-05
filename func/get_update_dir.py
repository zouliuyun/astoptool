#!/usr/bin/env python
#-*- coding:utf8 -*-
import os,sys,re,json

def check_less(dir,fromVersion):
    curDir = dir.split(".")
    fDir = fromVersion.split(".")
    for i in range(4):
        if int(curDir[i]) < int(fDir[i]):
            #print "less from",curDir[i],fDir[i],dir,fromVersion
            return False
        if int(curDir[i]) > int(fDir[i]):
            return True
    return True
def check_more(dir,toVersion):
    curDir = dir.split(".")
    tDir = toVersion.split(".")
    for i in range(4):
        if int(curDir[i]) > int(tDir[i]):
            #print "more to",curDir[i],tDir[i],dir,toVersion
            return False
        if int(curDir[i]) < int(tDir[i]):
            return True
    return True

def check_dir(dir,fromVersion,toVersion,clienttype,hd):
    if not check_less(dir,fromVersion):
        return False
    if toVersion != None and toVersion != "" and not check_more(dir,toVersion):
        return False
    #if str(hd).lower() != "true":
    #    if clienttype == "appstore64": 
    #        if not os.path.exists(dir + "/main.lua"):
    #            return False
    #    else:
    #        if os.path.exists(dir + "/main.lua"):
    #            return False
    #else:
    #    if clienttype == "appstore64" :
    #        #if not os.path.exists(dir + "/res/main.lua") and not os.path.exists(dir + "/hd_res/main.lua"):
    #        if not os.path.exists(dir + "/res_64") and not os.path.exists(dir + "/hd_res_64"):
    #            return False
    #    else:
    #        if os.path.exists(dir + "/res/main.lua") or os.path.exists(dir + "/hd_res/main.lua"):
    #            return False
    return True
def get_dirs(zip_www_dir,fromVersion,toVersion=None,type=None,hd=None):
    reReturn = {"result":True}
    if str(type).strip() in ["","none","null"] or str(hd).lower() not in ["true","false","none"]:
        reReturn["result"] = False
        reReturn["msg"] = "type:%s,hd:%s,can not be null"%(type,hd)
        return reReturn
    result = []
    if not os.path.exists(zip_www_dir):
        reReturn["msg"] =  "www dir %s not exists!"%zip_www_dir
        reReturn["result"] = False
        return reReturn
    os.chdir(zip_www_dir)
    for dir in os.listdir(zip_www_dir):
        if not os.path.isdir(dir):
            continue
        if not re.match(r'[0-9]+(\.[0-9]+){3}',dir):
            continue
        if check_dir(dir,fromVersion,toVersion,type,hd):
            result.append(dir)
    reReturn["dir"] = result
    return reReturn
if __name__ == "__main__":
    wwwRoot = sys.argv[1]
    fromVersion = sys.argv[2]
    toVersion = sys.argv[3]
    type = "" #主要区分appstore64跟appstore和jailbreak
    hd = "" #主要区分appstore64跟appstore和jailbreak
    if len(sys.argv) > 5:
        type = sys.argv[4]
        hd = sys.argv[5]
    print json.dumps(get_dirs(wwwRoot,fromVersion,toVersion,type,hd))
