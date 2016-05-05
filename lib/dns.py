#!/usr/bin/env python
#-*- coding:utf8 -*-

import state,ssh
from arg import *
import os

def execute(cmd):
    print cmd
    dnsip = mainOption("dnsip")
    dnsSsh = ssh.ssh(dnsip)
    try:
        return dnsSsh.cmd(cmd)
    except Exception,e:
        return 1,"执行失败",str(e)

def getDomain(game,server):
    yx,quhao = getYxNum(server)
    curdir = os.path.abspath(os.path.dirname(__file__))
    domain = os.popen("grep '%s@%s_' %s/../domain_list/special_list %s/../domain_list/all_game_domain_newserver|head -1"%(game,yx,curdir,curdir)).read().strip()
    if domain == "":
        return None
    else:
        s = domain.split("@")
        if len(s) < 4:
            return None
        else:
            return s[3].replace("${serverid}",quhao)
def addDns(game,dnsgame,server,ip,level,url=None):
    result = {"status":True,"msg":"添加成功"}
    if url:
        domain = url
    else:
        domain = getDomain(game,server)
        if domain == None:
            result["status"] = False
            result["msg"] = "获取域名失败"
            return result
        elif domain == "oversea":
            result["status"] = True
            result["msg"] = "海外游戏服，无需解析dns"
            return result
    status,out,err = execute("/app/opbin/dns/dnsapi -g %s -a add -d %s -l %s -i %s"%(dnsgame,domain,level,ip))
    if status == 0:
        if out.find("Record add success") < 0:
            result["status"] = False
            result["msg"] = out
    else:
        result["status"] = False
        result["msg"] = out
    return result
def upDns(game,dnsgame,server,ip,level,url=None):
    result = {"status":True,"msg":"修改成功"}
    if url:
        domain = url
    else:
        domain = getDomain(game,server)
        if domain == None:
            result["status"] = False
            result["msg"] = "获取域名失败"
            return result
        elif domain == "oversea":
            result["status"] = True
            result["msg"] = "海外游戏服，无需解析dns"
            return result
    status,out,err = execute("/app/opbin/dns/dnsapi -g %s -a up -d %s -l %s -i %s"%(dnsgame,domain,level,ip))
    if status == 0:
        if out.find("Record modify success") < 0:
            result["status"] = False
            result["msg"] = out
    else:
        result["status"] = False
        result["msg"] = out
    return result
def delDns(game,dnsgame,server,level,url=None):
    result = {"status":True,"msg":"删除成功"}
    if url:
        domain = url
    else:
        domain = getDomain(game,server)
        if domain == None:
            result["status"] = False
            result["msg"] = "获取域名失败"
            return result
        elif domain == "oversea":
            result["status"] = True
            result["msg"] = "海外游戏服，无需解析dns"
            return result
    status,out,err = execute("/app/opbin/dns/dnsapi -g %s -a del -d %s -l %s"%(dnsgame,domain,level))
    if status == 0:
        if out.find("Record delete success") < 0:
            result["status"] = False
            result["msg"] = out
    else:
        result["status"] = False
        result["msg"] = out
    return result
def disableDns(game,dnsgame,server,level,url=None):
    result = {"status":True,"msg":"禁用成功"}
    if url:
        domain = url
    else:
        domain = getDomain(game,server)
        if domain == None:
            result["status"] = False
            result["msg"] = "获取域名失败"
            return result
        elif domain == "oversea":
            result["status"] = True
            result["msg"] = "海外游戏服，无需解析dns"
            return result
    status,out,err = execute("/app/opbin/dns/dnsapi -g %s -a disable -d %s -l %s"%(dnsgame,domain,level))
    if status == 0:
        if out.find("Record disable success") < 0:
            result["status"] = False
            result["msg"] = out
    else:
        result["status"] = False
        result["msg"] = out
    return result
