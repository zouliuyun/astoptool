#!/usr/bin/env python
#-*- coding:utf8 -*-
'''

   新增，修改，查询 GW，Match 列表模块
   Kuangling created 2017-09-17

'''

import sys,os,json,commands,re,string,csv
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

#查询接口
def queryAction():
    print state.game,state.language,state.type
    print "开始调用查询语句..."
    sys.stdout.flush()
    cmdstr = 'curl -d \'game_flag=%s&lang=%s&type=%s\' http://42.62.92.221/gwmatch/queryGwOrMatch.action 2>/dev/null'%(state.game,state.language,state.type)
    datafileName=os.popen(cmdstr).readlines()
    filelist=datafileName[0][8:][:-16]
    x = json.loads(filelist)
    #print x
    fileName='%s_%s_%s_list'%(state.game,state.language,state.type)
    print fileName
    f = csv.writer(open(fileName, "wb+"))
    f.writerow(["游戏服名", "IP", "域名"])
    for i in x:
        if i["ip"] is None:
            i["ip"]=""
        elif i["domain"] is None:
            i["domain"]=""
        print i
        f.writerow([i["name"],
                    i["ip"],
                    i["domain"]])

#新增接口
def addAction():
    #cmdstr = 'curl -d \'game_flag=%s&lang=%s&type=%s&name=%s&ip=%s&domain=%s\' http://42.62.92.221/gwmatch/addGwOrMatch.action 2>/dev/null'%(state.game,state.language,state.type,state.name,state.ip,state.domain) 
    #print cmdstr
    #os.popen(cmdstr).readlines()
    print "开始调用添加语句..."
    sys.stdout.flush()
    status,out = commands.getstatusoutput("curl -d \'game_flag=%s&lang=%s&type=%s&name=%s&ip=%s&domain=%s\' http://42.62.92.221/gwmatch/addGwOrMatch.action 2>/dev/null"%(state.game,state.language,state.type,state.name,state.ip,state.domain))
    print out
    if status != 0:
        print "ERROR: 添加失败!"
        sys.exit(1)
    sys.stdout.flush()

#删除接口
def delAction():
    print "开始调用删除语句..."
    sys.stdout.flush()
    status,out = commands.getstatusoutput("curl -d \'game_flag=%s&lang=%s&type=%s&name=%s\' http://42.62.92.221/gwmatch/deleteGwOrMatch.action 2>/dev/null"%(state.game,state.language,state.type,state.name))
    print out

#修改接口
def modAction():
    print "开始调用修改语句..."
    sys.stdout.flush()
    if not null(state.ip):
        status,out = commands.getstatusoutput("curl -d \'game_flag=%s&lang=%s&type=%s&name=%s&ip=%s\' http://42.62.92.221/gwmatch/addGwOrMatch.action 2>/dev/null"%(state.game,state.language,state.type,state.name,state.ip))
    if not null(state.domain):
        print state.domain
        status,out = commands.getstatusoutput("curl -d \'game_flag=%s&lang=%s&type=%s&name=%s&domain=%s\' http://42.62.92.221/gwmatch/addGwOrMatch.action 2>/dev/null"%(state.game,state.language,state.type,state.name,state.domain))
    print out

def arg_init():
        parser = argparse.ArgumentParser()
        parser.add_argument("-g",dest="game",help="项目名:gcld,tjxs")
        parser.add_argument("-l",dest="language",help="语种:cn,vn,th")
        parser.add_argument("-a",dest="action",help="操作类型:query,add,delete,modify")
        parser.add_argument("-t",dest="type",help="分别类型:match|gw")
        parser.add_argument("-n",dest="name",help="Match名字:match_1|gw")
        parser.add_argument("-i",dest="ip",help="IP:192.168.1.1")
        parser.add_argument("-d",dest="domain",help="域名:match5.aoshitang.com")
        return parser.parse_args()

if __name__ == "__main__":
    args = arg_init()
    state.game = args.game
    state.language = args.language
    state.type = args.type
    state.name = args.name
    state.ip = args.ip
    state.domain = args.domain
    if args.action == 'query':
        queryAction()
    elif args.action == 'add':
        addAction()
    elif args.action == 'modify':
        modAction()
    elif args.action == 'delete':
        delAction()
