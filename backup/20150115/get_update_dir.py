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

def check_dir(dir,fromVersion,toVersion):
    if not check_less(dir,fromVersion):
        return False
    if toVersion != None and toVersion != "" and not check_more(dir,toVersion):
        return False
    return True
def get_dirs(zip_www_dir,fromVersion,toVersion=None):
    reReturn = {"result":True}
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
        if check_dir(dir,fromVersion,toVersion):
            result.append(dir)
    reReturn["dir"] = result
    return reReturn
if __name__ == "__main__":
    wwwRoot = sys.argv[1]
    fromVersion = sys.argv[2]
    toVersion = sys.argv[3]
    print json.dumps(get_dirs(wwwRoot,fromVersion,toVersion))
