#!/usr/bin/env python
#-*- coding:utf8 -*-
#-*- coding:utf8 -*-
'''
新增联运

2015-09-05 Xiaoyun Created
'''
from arg import *
import os,json,sys,urllib
import logging,datetime
import commands
import check,common,ssh,mailhtml,sendmail,serverlist,backstage,getip

class addPartner:
    def __init__(self,game,language,oldyx,newyx,official_url,addiction_url,bbs_url,cname,pay_url,allow_ip):
        '''新联运添加'''
        self.game = game
        self.language = language
        self.oldyx = oldyx
        self.newyx = newyx
        self.official_url = official_url
        self.addiction_url = addiction_url
        self.bbs_url = bbs_url
        self.cname = cname
        self.pay_url = pay_url
        self.allow_ip = allow_ip
    def init(self):
        curdir = os.path.dirname(os.path.abspath(__file__))
        self.curdir = curdir
        logdir = curdir +"/../logs"
        if not os.path.exists(logdir):
            os.makedirs(logdir)
        game = self.game
        language = self.language
        nowstring = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        logging.basicConfig(level=logging.INFO,
                format='%(asctime)s %(levelname)s %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                #filename='%s/addPartner_%s_%s_%s.log'%(os.path.abspath(logdir),game,newyx,nowstring),
                #filename='%s/addPartner_%s_%s.log'%(os.path.abspath(logdir),game,newyx),
                #filemode='a'
                )
        logging.info("开始新增联运...")
        print "详细日志为:%s/addPartner_%s_%s.log"%(os.path.abspath(logdir),game,self.newyx)
        sys.stdout.flush()
        self.html = mailhtml.mailhtml("%s_%s_addPartner.html"%(game,self.newyx),"%s_%s新联运添加"%(game,self.newyx))
        self.email_address = gameOption("email_address")
        self.mail_title = "[%s][%s]新联运添加"%(game,self.newyx)

        self.htmlStatus = True
        try:
            self.www_ssh_ip = gameOption("www_ssh_ip")
            logging.info("%s建立连接..."%self.www_ssh_ip)
            self.ssh = ssh.ssh(self.www_ssh_ip)
            logging.info("%s建立ssh连接完毕!"%self.www_ssh_ip)
            self.clientrootdir = mainOption("clientrootdir").replace("${game}",game)
            self.rootdir = mainOption("rootdir").replace("${game}",game)

            #后台相关信息
            self.backstage = gameOption("backstage")
            self.backstage_db = gameOption("backstage_db")
            self.backstage_tag = gameOption("backstage_tag",default="")
            self.backstage_interface_url = gameOption("backstage_interface_url")
            self.backstage_header = gameOption("backstage_header")
            self.have_backstage_interface = gameOption("have_backstage_interface",type="bool")

            #是否为海外
            self.is_oversea = gameOption("is_oversea",type="bool")
            #是否为手游
            if gameOption("is_mobile",type="bool"):
                self.is_mobile = "mobile"
                self.partnersType = 2
            else:
                self.is_mobile = "web"
                self.partnersType = 1

            #新联运添加脚本
            self.addPartner_script = gameOption("addPartner_script")
            #后台游戏域名，后续会替换server_url
            self.web_url = gameOption("web_url")
            logging.info("变量初始化完毕")
        except Exception,e1:
            self.statusCheck(False,str(e1))
        #print server_url,server_url_tag,title,server_url_tag

    def cmd(self,command,msg=""):
        '''执行命令，如果返回非0则发出邮件，并退出'''
        try:
            status,stdout,stderr = self.ssh.cmd(command)
            logging.info("[%s]\n%s"%(command,stdout))
            if status != 0:
                self.html.add(command,stderr+"\n"+msg,color="red")
                self.sendEmail(False)
                logging.error("[%s]\n%s"%(command,stderr+"\n"+msg))
                sys.exit(1) 
            else:
                return stdout
        except Exception,e1:
            self.html.add(command,str(e1)+"\n"+msg,color="red")
            self.sendEmail(False)
            logging.error("[%s]\n%s"%(command,str(e1)+"\n"+msg))
            sys.exit(1)
    def statusCheck(self,status,reason):
        if not status:
            self.html.add("错误描述",reason,color="red")
            self.sendEmail(False)
            logging.error(reason)
            sys.exit(1)
    def sendEmail(self,status,files=[]):
        if not status:
            sendmail.sendmail(self.html.getCon(),self.email_address,self.mail_title + "[Fail]","NEWSERVER@game-reign.com",files=files)
        else:
            sendmail.sendmail(self.html.getCon(),self.email_address,self.mail_title + "[Succ]","NEWSERVER@game-reign.com",files=files)
        logging.info("邮件已发送")
  
 #添加新联运方法
    def addBackstage(self):
        try:
            data = {}
            data["name"] = self.cname
            data["flag"] = self.newyx
            data["type"] = self.partnersType
            #data["lang"] = self.language
            header = {"Host":self.backstage_header}
            logging.info("后台信息:%s"%str(data))
            logging.info(urllib.urlencode(data))
            result = backstage.addPartner(self.backstage_interface_url,data,header)
            logging.info("后台接口调用结果:" + str(result["response"]))
            if result["status"]:
                self.html.add("后台添加","成功",color="green")
            else:
                self.html.add("后台添加",result["msg"],color="red")
                self.htmlStatus = False
        except Exception,e1:
            self.html.add("后台添加",str(e1),color="red")
            self.htmlStatus = False
    

    def run(self):
        self.init() 
        self.cmd("test -e /app/www/%s/newserver/%s/properties/%s.properties"%(self.game,self.language,self.oldyx),"参照联运的properties模板不存在")
        self.cmd("test -e /app/www/%s/newserver/%s/template/%s.tgz"%(self.game,self.language,self.oldyx),"参照联运的gametemplate模板不存在")
        self.cmd("test -e /app/www/%s/newserver/%s/www/www_%s.tgz"%(self.game,self.language,self.oldyx),"参照联运的www模板不存在")
        self.cmd("test ! -e /app/www/%s/newserver/%s/properties/%s.properties"%(self.game,self.language,self.newyx),"参照联运的properties模板已经存在")
        self.cmd("test ! -e /app/www/%s/newserver/%s/template/%s.tgz"%(self.game,self.language,self.newyx),"参照联运的gametemplate模板已经存在")
        self.cmd("test ! -e /app/www/%s/newserver/%s/www/www_%s.tgz"%(self.game,self.language,self.newyx),"参照联运的www模板已经存在")
        try:
            self.ssh.put("%s/../shell/%s"%(self.curdir,self.addPartner_script),remote_path="/app/www/%s/newserver/%s"%(self.game,self.language))
        except Exception,e1:
            self.statusCheck(False,str(e1)+"\nscp %s到服务器失败"%(self.addPartner_script))
        newpartner_parameter = " '%s' '%s' '%s'  '%s'  '%s' '%s' '%s' '%s' '%s' '%s'"%(self.game,self.language,self.oldyx,self.newyx,self.official_url,self.addiction_url,self.bbs_url,self.cname,self.pay_url,self.allow_ip)
        print newpartner_parameter
        addPartner_stdout = self.cmd("source /etc/profile && sh /app/www/%s/newserver/%s/%s %s"%(self.game,self.language,self.addPartner_script,newpartner_parameter), msg="布服模板生成失败!")
        self.html.add("新联运添加结果","成功",color="green")
        if addPartner_stdout.find("www模板生成失败") >= 0:
            self.html.add("www模板","失败",color="red")
            self.htmlStatus = False
        if addPartner_stdout.find("gametemplate生成失败") >= 0:
            self.html.add("gametemplate生成","失败",color="red")
            self.htmlStatus = False
        if addPartner_stdout.find("properties生成失败") >= 0:
            self.html.add("properties生成","错误",color="red")
            self.htmlStatus = False
        if self.have_backstage_interface:
            logging.info("开始添加后台...")
            self.addBackstage()
            logging.info("后台添加完毕!")
        remotefile = "/app/www/%s/newserver/%s/key/%s_%s对接key.txt" %(self.game,self.language,self.game,self.cname)
        localfile = os.path.basename(remotefile)
        cmd = "scp astd@%s:%s ./%s"%(self.www_ssh_ip,remotefile,localfile)
        try:
            os.system(cmd)
        except Exception,e1:
            self.html.add("scp联运key文件",str(e1),color="red")
        self.html.add("key请参照附件","成功",color="green")
        self.sendEmail(self.htmlStatus,files=[localfile])
        os.remove(localfile)
        logging.info("添加完毕!")
