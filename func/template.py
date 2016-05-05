#!/usr/bin/env python
#-*- coding:utf8 -*-

from arg import *
import check,serverlist,state
import os,sys
import ssh
import logging

class template:
    def __init__(self,game,language,servername,ip=None,port=22,mainServername=None):
        #logging.basicConfig(level=logging.INFO,
        #        format='%(asctime)s %(levelname)s %(message)s',
        #        datefmt='%Y-%m-%d %H:%M:%S',
        #        )
        self.game = game
        self.language = language
        self.servername = servername
        self.ip = ip
        self.rootDir = mainOption("rootdir").replace("${game}",game)
        self.commonPath = "newserver/%s/common"%language
        self.templatePath = "newserver/%s/template"%language
        self.propertiesPath = "newserver/%s/properties"%language
        self.wwwPath = "newserver/%s/www"%language
        self.yx,self.quhao = getYxNum(servername)
        if not check.nullCheck(mainServername):
            self.mainServer = game + "_" + mainServername
        else:
            self.mainServer = None
        if not check.checkServer(str(servername)):
            print "请输入正确的游戏服名称"
            #logging.error("请输入正确的游戏服名称")
            sys.exit(1)
        #if not check.checkIp(str(ip)):
        if ip == None:
            backstage_db = gameOption("backstage_db")
            backstage_tag = gameOption("backstage_tag")
            is_mobile = gameOption("is_mobile",type="bool")
            if is_mobile:
                partnersType = 2
            else:
                partnersType = 1
            backstage_ip = gameOption("backstage")
            print backstage_db,backstage_tag,partnersType,"mix",backstage_ip,servername
            serverList = serverlist.serverRange(backstage_db,backstage_tag,partnersType,"mix",backstage_ip,serverlist=servername)
            if len(serverList) != 1:
                print "ERROR: 获取服务器ip失败或者不唯一",serverList
                sys.exit(1)
            else:
                self.ip = serverList[0][1]
        self.ssh = ssh.ssh(self.ip,port=port)
        self.www_dir_type = gameOption("www_dir_type")
        www_ip = gameOption("www_ip")
        www_ssh_ip = gameOption("www_ssh_ip")
        www_port = gameOption("www_port",default="80")
        www_ssh_port = gameOption("www_ssh_port",default="22")
        self.www_root = gameOption("www_root")
        self.template_tar_dir = gameOption("template_tar_dir").replace(" ","").split(",")
        self.template_exclude_dir = gameOption("template_exclude_dir").replace(" ","").split(",")
        self.www_ssh = ssh.ssh(www_ssh_ip,port=int(www_ssh_port))
    def chdir(self,dir):
        if not os.path.exists( dir ) or not os.path.isdir(dir):
            os.makedirs(dir)
            os.system("chown astd.astd -R "+dir)
        os.chdir(dir)
    def cmd(self,command):
        status,stdout,stderr = self.ssh.cmd(command)
        #logging.info("[%s]"%command)
        #logging.info(stdout)
        sys.stdout.write("[%s]\n"%command)
        sys.stdout.write(stdout)
        if status != 0:
            #sys.stdout.write("%s 执行结果失败!"%command)
            #sys.stdout.write(stderr)
            #logging.error(stderr)
            #sys.exit(1)
            raise Exception("[%s]执行失败!Err:%s"%(command,stderr))
    def fileGet(self,gamepath,file,wwwpath):
        #logging.info("开始scp %s ..."%file)
        print "开始scp %s ..."%file
        localPath = "%s/%s"%(self.rootDir,wwwpath)
        self.chdir(localPath)
        self.ssh.get("%s/%s"%(gamepath,file),local_path=localPath)
        os.system("chown astd.astd %s/%s" %(localPath,file) )
        self.www_ssh.cmd("mkdir -p '%s/%s/%s'"%(self.www_root,self.game,wwwpath))
        #logging.info("开始scp到www服务器...")
        print ("开始scp到www服务器...")
        self.www_ssh.put("%s/%s/%s"%(self.rootDir,wwwpath,file),remote_path = "%s/%s/%s"%(self.www_root,self.game,wwwpath))
        #logging.info("scp %s 完成"%file)
        print ("scp %s 完成"%file)
    def updateServerLib(self):
        '''更新游戏服的通用包,bootstrap.jar,lib目录，font目录'''
        serverRootDir = "/app/%s_%s"%(self.game,self.servername)
        self.cmd("test -d %s"%serverRootDir)
        self.ssh.setprogress(True)
        self.www_ssh.setprogress(True)
        for file in self.template_tar_dir:
            if file.strip() == "":
                continue
            path = os.path.dirname(file)
            filename = os.path.basename(file)
            self.cmd("cd %s/%s && rm -f %s.tgz && tar zcf %s.tgz %s"%(serverRootDir,path,filename,filename,filename))
            self.fileGet("%s/%s"%(serverRootDir,path),"%s.tgz"%filename,self.commonPath)
            self.cmd("cd %s/%s && rm -f %s.tgz "%(serverRootDir,path,filename))
        self.ssh.setprogress(False)
        self.www_ssh.setprogress(False)
        #self.cmd("cd %s/backend/ && rm -f lib.tgz && tar zcf lib.tgz lib && cd apps && rm -f font.tgz && tar zcf font.tgz font"%serverRootDir)
        #self.fileGet("%s/backend"%serverRootDir,"lib.tgz",self.commonPath)
        #self.fileGet("%s/backend"%serverRootDir,"bootstrap.jar",self.commonPath)
        #self.fileGet("%s/backend/apps"%serverRootDir,"font.tgz",self.commonPath)
    def updateServerNginxConf(self):
        self.cmd("cp /app/nginx/conf/vhost/%s_%s.conf /app/%s_%s/nginx_template.conf"%(self.game,self.servername,self.game,self.servername))
        self.fileGet("/app/%s_%s"%(self.game,self.servername),"nginx_template.conf",self.commonPath)
        self.cmd("rm /app/%s_%s/nginx_template.conf"%(self.game,self.servername))
    def updateServerSql(self):
        '''更新游戏服的建库sql'''
        serverRootDir = "/app/%s_%s"%(self.game,self.servername)
        self.cmd("test -d %s"%serverRootDir)
        self.cmd("mkdir -p /app/opbin/workspace")
        self.cmd("pandora --dump -R --opt -d %s_%s > /app/opbin/workspace/%s_%s_init.sql"%(self.game,self.servername,self.game,self.language))
        self.cmd("sed -i 's/AUTO_INCREMENT=[0-9]*\s//g' /app/opbin/workspace/%s_%s_init.sql"%(self.game,self.language))
        try:
            self.cmd("version=$(pandora %s_%s -e 'select db_version from db_version' |grep  [0-9]) && echo \"insert into db_version(db_version) values('$version');\" >> /app/opbin/workspace/%s_%s_init.sql" %(self.game,self.servername,self.game,self.language))
        except Exception,e1:
            if not str(e1).find("db_version' doesn't exist") :
                raise e1
            else:
                print "Warnning:%s"%str(e1)
        self.fileGet("/app/opbin/workspace","%s_%s_init.sql"%(self.game,self.language),self.commonPath)
        self.cmd("rm -f /app/opbin/workspace/%s_%s_init.sql"%(self.game,self.language))
    def updateServerConf(self):
        '''更新游戏服的配置文件目录'''
        serverRootDir = "/app/%s_%s"%(self.game,self.servername)
        self.cmd("test -d %s"%serverRootDir)
        excludepath = "--exclude=backend/apps/*.bak --exclude=backend/apps/*.back --exclude=backend/*.tgz --exclude=backend/apps/*.tgz --exclude=backend/apps/*.sql"
        for file in self.template_tar_dir + self.template_exclude_dir:
            if file.strip() == "":
                continue
            excludepath += " --exclude=" + file.strip()
        self.cmd("cd /app/%s_%s && rm -f %s.tgz && grep -E 'serverid\s*=' backend/apps/* | cut -d':' -f1 > excludefile && tar zcf %s.tgz --exclude-from=excludefile %s backend && rm excludefile"%(self.game,self.servername,self.yx,self.yx,excludepath))
        self.fileGet(serverRootDir,"%s.tgz"%self.yx,self.templatePath)
        self.cmd("cd /app/%s_%s && rm -f %s.tgz "%(self.game,self.servername,self.yx))
    def getMainServername(self):
        if not self.mainServer:
            status,mainServer,stderr = self.ssh.cmd("grep -E 'TOMCAT_PATH\[%s\]' /app/%s_backstage/socket_gameserver.ini|cut -d '/' -f3"%(self.servername.replace("_","_S"),self.game))
            if status !=0 or mainServer == "":
                raise Exception("获取主服名称失败")
            else:
                self.mainServer = mainServer.strip()
    def updateServerProperties(self):
        '''更新游戏服从服的配置文件'''
        self.getMainServername()
        self.cmd("test -d /app/%s"%self.mainServer)
        self.fileGet("/app/%s/backend/apps/"%self.mainServer.strip(),"%s.properties"%self.yx,self.propertiesPath)
        
    def updateServerWww(self):
        '''更新游戏服的前段www配置'''
        self.getMainServername()
        self.cmd("test -d /app/%s"%self.mainServer)
        gameWwwDir = ""
        if self.www_dir_type == "old":
            gameWwwDir = "www"
        else:
            gameWwwDir = "www_" + self.servername
        self.cmd("cd /app/%s/%s && rm -f www_%s.tgz && tar zcf www_%s.tgz --exclude=*.bak --exclude=*.back --exclude=*.tgz --exclude=*.sql --exclude=*.conf --exclude=gcld_mobile_feiliu --exclude=*.gz --exclude=*.zip *"%(self.mainServer,gameWwwDir,self.yx,self.yx))
        self.fileGet("/app/%s/%s"%(self.mainServer,gameWwwDir),"www_%s.tgz"%self.yx,self.wwwPath)
        self.cmd("cd /app/%s/%s && rm -f www_%s.tgz "%(self.mainServer,gameWwwDir,self.yx))

if __name__ == "__main__":
    t = template("tjxs","cn","37wan_1",ip="10.6.197.215")
    t.updateServerNginxConf()
