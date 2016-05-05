#!/usr/bin/env python
#-*- coding:utf8 -*-

import ssh,state,common
from arg import *
import paramiko
import os
import time

def download_mysql(failurIp,database,backup_date):
    curdir = os.path.abspath(os.path.dirname(__file__))
    s = ssh.ssh(failurIp,user='root')
    s.put("%s/../shell/copy_database.sh"%curdir,remote_path="/app")

    database_list = []
    os.popen("pandora -e 'use acegi_gcmob;select concat(server_flag,'_',replace(name,'S','')) from server where n_ip = %s and server.status&1=1 and istest = 0 and server.mixflag = 1;' > /tmp/get_database.txt"%failurIp).read()
    database_file = file('/tmp/get_database.txt')
        for line in database_file.readlines():
            datbase_list.append(line)
    database_file.close()
    
    serverlist = " ".join(database_list)
    s.cmd("sh /app/copy_database.sh %s %s"%(serverlist,backup_date))
    s.cmd("rsync -av /tmp/*  %s:/tmp"%recoverIp)

def recover(recoverIp):
    curdir = os.path.abspath(os.path.dirname(__file__))
    s = ssh.ssh(recoverIp,user='root')
    s.put("%s/../shell/recoverMysql.sh"%curdir,remote_path="/app")
    s.cmd('sh /app/recoverMysql.sh') 
    s.close()

def mysqlRecover(failurIp,recoverIp,database='',backup_date):
    download_mysql(failurIp,recoverIp)
    recover(recoverIp)
