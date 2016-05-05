#!/usr/bin/env python
#-*- coding:utf8 -*-

from arg import *
#import check,serverlist,state
import os,sys
import ssh
import logging

class kfgz:
    def __init__(self,game,language,level,days,serverDate,hfdate):
        self.game = game
        self.language = language
        self.level = level
        self.days = days
        self.kfdate = serverDate
        self.hfdate = hfdate
    def init(self):
        self.clientrootdir = mainOption("clientrootdir").replace("${game}",self.game)
        curdir = os.path.dirname(os.path.abspath(__file__))
        self.curdir = curdir
        self.kfgz_script = 'gcld_kfgz_match.py'
        self.kfgz_config = 'gcld_kfgz.conf'
        self.backstage_ip = gameOption("backstage")
        self.ssh = ssh.ssh(self.backstage_ip,port=22,closegw=True)
        logging.basicConfig(level=logging.INFO,
                format='%(asctime)s %(levelname)s %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                )

    def cmd(self,command):
        status,stdout,stderr = self.ssh.cmd(command)
        sys.stdout.write("[%s]\n"%command)
        sys.stdout.write(stdout)
        if status != 0:
            raise Exception("[%s]执行失败!Err:%s"%(command,stderr))
        logging.info(stdout)
    def gcld_kfgz_match(self):
        remote_script=self.clientrootdir+"/kfgz/"+self.kfgz_script
        self.cmd("[ -d %s/kfgz ] || mkdir -p  %s/kfgz"%(self.clientrootdir,self.clientrootdir))
        #print "开始scp %s ..."% remote_script
        logging.info('开始scp %s ...'%remote_script)
        self.ssh.put("%s/../shell/%s"%(self.curdir,self.kfgz_script),remote_path=self.clientrootdir+"/kfgz")
        self.ssh.put("%s/../conf/%s"%(self.curdir,self.kfgz_config),remote_path=self.clientrootdir+"/kfgz")
        logging.info('scp %s 完成'%remote_script)
        command='/usr/local/bin/python ' + remote_script + ' -g ' + self.game + ' -L ' + self.language + ' -l ' + self.level + ' -n ' + self.days + ' -d ' +'"' + self.kfdate +'"' + ' -H ' + '"'  + self.hfdate + '"'
        #print ("请等待，开始进行跨服排赛...")
        logging.info('请等待，开始进行跨服排赛...')
        sys.stdout.flush()
        self.cmd(command)
        logging.info('跨服排赛完成,请查收邮件！')
        #print ("跨服排赛完成,请查收邮件！")
    def run(self):
        self.init()
        self.gcld_kfgz_match()
if __name__ == "__main__":
    t = kfgz("gcld","tw",80,7,"2015-03-01 23:59:59","2015-02-15 23:59:59")
    t.gcld_kfgz_match()
