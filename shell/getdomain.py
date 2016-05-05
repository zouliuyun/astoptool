#!/usr/bin/env python
#-*- coding:utf8 -*-

from bible import state,ssh
from bible.arg import *
import os,sys,re,threading,Queue,datetime

def check_server(server,backstage,backstage_close_gw):
    if server.strip() == "":
        return
    specialflag=0
    flagspecial=0
    errorflag=0
    server_s = server.split("@")
    servername = server_s[0]
    tomcat = server_s[1]
    serverip = server_s[2]
    serverurl = server_s[3]

    server_id = servername.split("_")[1]
    server_yx = servername.split("_")[0]
    backstageSsh = ssh.ssh(backstage,closegw=backstage_close_gw)

    if serverurl.startswith("s%s."%server_id):
        gameserverurl = serverurl.replace("s%s."%server_id,"s${serverid}.")
    else:
        specialflag=1
        errorcode = "gameserverurl %s not starts with s%s. "%(serverurl,server_id)

    status,servercname,error=backstageSsh.cmd("dig %s | grep '.aoshitang.com.' | tail -1  | awk '{print $1}' | sed 's/.aoshitang.com.$//g'"%(serverurl,))
    if is_oversea :
        servercname="oversea"
    elif servercname.find("s%s."%server_id) != 0:
        specialflag=1
        errorcode = "servercname %s not starts with s%s. "%(servercname,server_id)
    else:
        servercname=servercname.replace("s%s."%server_id,"s${serverid}.").strip()

    if www_dir_type == "old":
        mainhtml = "/app/%s_%s/www/Main.html"%(game,tomcat)
    else:
        mainhtml = "/app/%s_%s/www_%s/Main.html"%(game,tomcat,servername)
    serverssh = ssh.ssh(serverip)
    if big_mix_server:
        if tomcat == servername:
            status,title,error = serverssh.cmd("grep '<title>' %s|sed 's/<title> *//g;s/ *<\/title>//g'"%(mainhtml,))
        else:
            return
    else:
        status,title,error=serverssh.cmd("grep '<title>' %s|sed 's/<title> *//g;s/ *<\/title>//g'"%(mainhtml,))
    
    title = title.strip().replace("%s区"%server_id,"${serverid}区").replace("%s服"%server_id,"${serverid}服")
    if not title or title == "":
        specialflag=1
        errorcode = "title is null"
    
    if specialflag != 1:
        url_template_tmp.write("%s@%s@%s@%s@%s\n"%(game,servername,gameserverurl,servercname,title))
    else:
        oldline = os.popen("grep '^%s@%s_' %s"%(game,server_yx,old_url_template_tmp)).read()
        if oldline.strip() != "":
            print "%s get old line:%s"%(server,oldline)
            url_template_tmp.write(oldline)
        else:
            print servername,errorcode,"\n"
if __name__ == "__main__":
    print "开始生成域名模板",datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    CONF_DIR=os.path.abspath(os.path.dirname(__file__)) + "/../conf"
    WORK_HOME=os.path.abspath(os.path.dirname(__file__)) + "/../domain_list"
    os.chdir(CONF_DIR)
    if not os.path.exists(WORK_HOME):
        os.mkdir(WORK_HOME)
    cmdstr = 'ls %s | grep -Ev "conf.tmp|logger.conf|main.conf|gcld_kfgz.conf" | sed "s/\(.*\)\.conf/\\1/g"'%CONF_DIR
    games = os.popen(cmdstr).readlines()
    
    old_url_template_tmp = WORK_HOME + "/all_game_domain_newserver"
    url_template_tmp_file = WORK_HOME + "/domain_temp"
    url_template_tmp = open(url_template_tmp_file,"w")
    for game in games:
        game = game.strip()
        print "start update game %s"%game
        state.gameconf = None
        state.mainconf = None
        state.game = game
        subs=os.popen("grep '\[.*\]' %s.conf | grep -v '\[common\]' | sed 's/\[\(.*\)\]/\\1/g'"%game).readlines()
        for language in subs:
            language = language.strip()
            print "start language %s..."%language
            try:
                state.language = language
                big_mix_server = gameOption("big_mix_server",type="bool")
                backstage = gameOption("backstage")
                backstage_db = gameOption("backstage_db")
                is_oversea = gameOption("is_oversea",type="bool")
                backstage_tag = gameOption("backstage_tag")
                www_dir_type = gameOption("www_dir_type")
                backstage_close_gw = gameOption("backstage_close_gw",default=False,type="bool")
            except Exception,e1:
                print str(e1)
                continue
    
            if backstage.strip() == "":
                continue
            try:
                backstageSsh = ssh.ssh(backstage,closegw=backstage_close_gw)
            except Exception,e1:
                print str(e1)
                continue
            
            sqlstr = 'select concat(server.server_flag,\"_\",server.name),server.server_name, server.n_ip,web_url from server join partners on server.server_flag=partners.flag where server.status&1=1 and server.istest=0 and server.mixflag=1 and partners.name like \"%s%%\" and partners.status=1 group by server.server_flag;'%backstage_tag
            statues,servers,error = backstageSsh.cmd("pandora %s -e '%s' | grep -v 'concat(server.server_flag'|sed 's/\t/@/g;s/_S/_/g;s#http://##g;s#https://##g;s#/root.*##g'"%(backstage_db,sqlstr))
            queue = Queue.Queue()
            for server in servers.split("\n"):
                if queue.qsize() > 40:
                    t = queue.get()
                    t.join()
                t = threading.Thread(target=check_server,args=(server,backstage,backstage_close_gw))
                t.start()
                queue.put(t)
            for i in range(queue.qsize()):
                queue.get().join()
    url_template_tmp.close()
    os.system("cp %s %s/bak/%s"%(old_url_template_tmp,WORK_HOME,datetime.datetime.now().strftime("%Y%m%d_%H%M%S.bak")))
    os.system("mv %s %s"%(url_template_tmp_file,old_url_template_tmp))
