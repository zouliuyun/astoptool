#!/usr/bin/env python
#-*- coding:utf8 -*-

from arg import *
import check,ssh
import sys,os,datetime,backstage

def cmd(cmdstr):
    status,out,err = sshobj.cmd(cmdstr)
    sys.stdout.write( "[%s]\n%s"%(cmdstr,out))
    sys.stdout.flush()
    if status != 0:
        raise Exception("ERROR:\n%s"%err)
    return out
def reset(cleartime,starttime,server):
    if check.nullCheck(cleartime):
        raise Exception("清档时间不能为空")
    if check.nullCheck(starttime):
        raise Exception("开服时间不能为空")
    if check.nullCheck(server):
        raise Exception("游戏服不能为空")
    if not check.checkDatetime(cleartime):
        raise Exception("清档时间格式不正确")
    if not check.checkDatetime(starttime):
        raise Exception("开服时间格式不正确")
    backstageIp = gameOption("backstage")
    backstageDb = gameOption("backstage_db")
    head_tag = gameOption("backstage_tag")
    ismobile = gameOption("is_mobile",type="bool")
    if ismobile:
        partnersType = 2
    else:
        partnersType = 1
    serverinfo = serverlist.serverInfo(backstageDb,head_tag,partnersType,"main",backstageIp,server)
    if not serverinfo["result"]:
        raise Exception("获取游戏服在后台的信息失败!msg:%s"%serverinfo["msg"])
    ip = serverinfo["ip"]
    if not check.checkIp(ip):
        raise Exception("获取游戏服ip失败!ip:%s"%ip)
    global sshobj
    sshobj = ssh.ssh(ip)
    players = cmd("pandora %s_%s -e 'select count(1) from player' | grep -v count"%(state.game,server)).strip()
    if players != "":
        if int(players) > 0:
           print "WARNNING: 当前角色数为%s"%players
    servertime = cmd("date +'%Y-%m-%d %H:%M:%S'").strip()
    print "servertime:",servertime
    servertime_datetime = datetime.datetime.strptime(servertime,"%Y-%m-%d %H:%M:%S")
    cleartime_datetime = datetime.datetime.strptime(cleartime,'%Y-%m-%d %H:%M:%S') 
    if servertime_datetime + datetime.timedelta(minutes=1) > cleartime_datetime :
        raise Exception("服务器时间大于了清档时间，清档失败!服务器时间为:%s,清档时间提交为:%s"%(servertime,cleartime))
    clearshell = gameOption("clear_script")
    print clearshell
    cmd("mkdir -p /app/opbin/%s/allinone/shell/"%state.game)
    sshobj.put("%s/../shell/%s"%(os.path.abspath(os.path.dirname(__file__)),clearshell),remote_path="/app/opbin/%s/allinone/shell/"%state.game)
    tmpfile = "/tmp/crontab_%s"%datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        cmd("crontab -l > %s"%tmpfile)
    except Exception,e1:
        if str(e1).find("no crontab for astd") < 0:
            raise e1
    backupCrontab = "/app/opbak/crontab/%s"%state.game
    cmd("mkdir -p %s"%backupCrontab)
    cmd("cp %s %s/"%(tmpfile,backupCrontab))
    cmd("mkdir -p /app/opbin/%s/allinone/logs/"%state.game)
    cmd('sed -i "/\\/app\\/opbin\\/%s\\/allinone\\/shell\\/%s\\s*\'%s\'\\s*\'%s\'/d" %s'%(state.game,clearshell,state.game,server,tmpfile))
    cronttime = cleartime_datetime.strftime("%M %H %d %m")
    cmd('echo "%s * sh /app/opbin/%s/allinone/shell/%s \'%s\' \'%s\' \'%s\' \'%s\' \'%s\' \'%s\' &>/app/opbin/%s/allinone/logs/clear_%s_info.log" >> %s'%(cronttime,state.game,clearshell,state.game,server,state.language,gameOption("www_ip"),gameOption("www_port"),gameOption("www_header"),state.game,server,tmpfile))
    cmd("crontab %s"%tmpfile)
    cmd("rm -f %s"%tmpfile)
    cmd('crontab -l | grep "%s.*\'%s\'"'%(clearshell,server))
    houtaiStarttime = (datetime.datetime.strptime(starttime,"%Y-%m-%d %H:%M:%S") - datetime.timedelta(minutes = 30)).strftime("%Y-%m-%d %H:%M:%S")
    data = {}
    data["servername"] = server.replace("_","_S")
    data["start_time"] = houtaiStarttime
    header = {"host":gameOption("backstage_header")}
    backstage_interface_url = gameOption("backstage_interface_url")
    houtai = backstage.upBackstage(backstage_interface_url,data,header)
    if houtai["status"]:
        print "后台修改成功"
    else:
        raise Exception("后台修改失败!msg:%s"%houtai["msg"])
