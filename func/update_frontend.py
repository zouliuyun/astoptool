#!/usr/bin/env python
#-*- coding:utf8 -*-
import sys,os,json,commands,re
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)) + "/../lib")
import optparse
import argparse
from arg import *
import state,common

def null(Str):
    if Str == None or str(Str).lower().strip() == "none" or str(Str).strip() == "" or str(Str).lower().strip() == "null":
        return True
    else:
        return False
def nullCheck(str,msg):
    if null(str):
        print "ERROR: " + msg
        sys.exit(1)
def checkFrontBackendVersion(versionStr):
    if not null(versionStr):
        if not re.match(r'^%s_[^/]*$'%state.game,versionStr):
            return False
    return True
def update(frontName):
    if not null(frontName):
        state.language = frontName.split("_")[1].strip()
        changefrontName = "-".join(frontName.split("-")[0:3]).strip()
        print state.game,state.language
        try:
            gateway = gameOption('gateway')
        except:
            gateway = None
        if gateway == 'ast_hk':
            front_script='online.frontend_gchw_V2'
        elif state.game == 'gcld' and  state.language == 'tw':
            front_script='online.frontend_gctw_V2'
        else:
            front_script='online.frontend'
        if not checkFrontBackendVersion(changefrontName):
            raise Exception("ERROR: [%s] 前端版本格式不正确"%changefrontName)
        print "/app/online/%s/frontend/%s"%(state.game,frontName.strip())
        print front_script
        #if os.path.exists("/app/online/%s/frontend/%s"%(state.game,frontName.strip())):
        print "开始调用前端脚本..."
        sys.stdout.flush()
        status,out = commands.getstatusoutput("sh /app/opbin/rundeck/%s -g %s -t %s"%(front_script,state.game,frontName.strip()))
        print out
        if status != 0:
            print "ERROR: 前端包%s上传失败!"%frontName.strip()
            sys.exit(1)
        sys.stdout.flush()

def arg_init():
        parser = argparse.ArgumentParser()
        parser.add_argument("-g",dest="game",help="项目名")
        parser.add_argument("-t",dest="target",help="前端目录名")
        return parser.parse_args()

if __name__ == "__main__":
    args = arg_init()
    state.game = args.game
    target = args.target
    update(target)
