#!/usr/bin/env python
#-*- coding:utf8 -*-

from arg import *
import os,json,shutil
import logging,datetime
import commands
import check,common,ssh,mailhtml,sendmail,serverlist

class deploy:
    def __init__(self,game,language,servername,mainserver,restart,title,gameurl,asturl,skipcheck):
        '''游戏混服部署任务
            如果为普通混服，则servername必须是一个游戏服，比如uc_1
            如果为大混服，则servername可以为多个游戏服，各游戏服之间使用逗号隔开，比如uc_1,jinli_1,...
            因为普通服需要获取域名信息，所以不能同时部署多个游戏混服
            mainserver为主服，比如feiliu_1
        '''
        self.game = game
        self.language = language
        self.servername = servername
        self.mainserver = mainserver
        self.title = title
        self.server_url = gameurl
        self.asturl = asturl
        self.skipcheck = skipcheck
        self.restart = restart
    def init(self):
        self.mainserverYx,self.mainserverQuhao = self.mainserver.split("_")
        self.htmlStatus = True
        curdir = os.path.dirname(os.path.abspath(__file__))
        self.curdir = curdir
        logdir = curdir +"/../logs"
        if not os.path.exists(logdir):
            os.makedirs(logdir)
        game = self.game
        servername = self.servername
        language = self.language
        nowstring = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        logging.basicConfig(level=logging.INFO,
                format='%(asctime)s %(levelname)s %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                filename='%s/mix_%s_%s.log'%(os.path.abspath(logdir),game,self.mainserver),
                filemode='a')
        logging.info("开始部署游戏...")
        self.html = mailhtml.mailhtml("mix_%s_%s_%s_deploy.html"%(game,self.mainserver,nowstring),"%s_%s游戏混服部署"%(game,self.mainserver))
        self.rootDir = mainOption("rootdir").replace("${game}",game)
        self.email_address = gameOption("email_address")
        self.mail_title = "[%s][%s]游戏服部署"%(game,servername)
        self.html.add("游戏混服名称",servername.replace(",","<br>"))
        self.htmlStatus = True
        try:
            self.clientrootdir = getOption(mainConfig,"main","clientrootdir").replace("${game}",game)
            self.rootdir = getOption(mainConfig,"main","rootdir").replace("${game}",game)

            #是否为大混服
            self.bigmix = gameOption("big_mix_server",type = "bool")
            if self.bigmix:
                self.html.add("混服类型","大混服")
            else:
                self.html.add("混服类型","混服")
            #参数校验
            self.sList = [ i.strip() for i in self.servername.split(",") if i.strip() != "" ]
            if self.bigmix:
                for i in self.sList:
                    self.statusCheck(check.checkServer(i),"游戏名称:%s 不合法"%i)
            else:
                self.statusCheck(check.checkServer(self.servername),"游戏名称:%s 不合法"%self.servername)
            #后台相关信息
            self.backstage = gameOption("backstage")
            self.backstage_db = gameOption("backstage_db")
            self.backstage_tag = gameOption("backstage_tag")
            self.backstage_interface_url = gameOption("backstage_interface_url")
            self.backstage_header = gameOption("backstage_header")
            self.have_backstage_interface = gameOption("have_backstage_interface",type="bool")
            #游戏服务器需要下载资源的地址信息
            self.www_ip = gameOption("www_ip")
            self.www_port = gameOption("www_port")
            self.www_header = gameOption("www_header")
            #是否为海外
            self.is_oversea = gameOption("is_oversea",type="bool")
            #是否为手游
            if gameOption("is_mobile",type="bool"):
                self.partnersType = 2
                self.is_mobile = "mobile"
            else:
                self.is_mobile = "web"
                self.partnersType = 1
            if self.skipcheck:
                serverExistsJson = json.loads(serverlist.serverListExists(self.backstage_db,self.backstage_tag,self.partnersType,servername,self.backstage))
                if serverExistsJson["result"]:
                    self.statusCheck(False,"游戏已经存在，请确认")
            #获取主服的信息
            #print self.backstage_db,self.backstage_tag,self.partnersType,"main",self.backstage,self.mainserver
            serverinfo = serverlist.serverInfo(self.backstage_db,self.backstage_tag,self.partnersType,"main",self.backstage,self.mainserver)
            logging.info(serverinfo)
            if not serverinfo["result"]:
                self.statusCheck(False,"主服信息获取失败,err:%s"%serverinfo["msg"])
            self.ip = serverinfo["ip"]
            self.statusCheck(check.checkIp(self.ip),"ip:%s不合法"%self.ip)
            self.starttime = serverinfo["starttime"]
            self.statusCheck(check.checkDatetime(self.starttime),"开服时间:%s 不合法"%self.starttime)
            self.mainserver_web_url = serverinfo["web_url"]
            self.html.add("服务器ip",self.ip)
            logging.info("%s建立ssh连接..."%self.ip)
            self.ssh = ssh.ssh(self.ip)
            logging.info("%s建立ssh连接完毕!"%self.ip)

            time_zone = gameOption("time_zone")
            delta_hours = 8 - int(time_zone)
            self.cleartime = (datetime.datetime.strptime(self.starttime,"%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=delta_hours) - datetime.timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
            self.html.add("开服时间(北京+8区)",self.starttime)
            self.html.add("清档时间(服务器%s区)"%time_zone,self.cleartime)
            #www是老模式(www)还是新模式(www_ly_id)
            self.www_dir_type = gameOption("www_dir_type")
            #是否添加ast域名解析
            self.add_dns = gameOption("add_dns",type="bool")
            #是否需要联运解析域名
            self.lianyun_add_dns = gameOption("lianyun_add_dns",type="bool")
            #后台游戏域名，后续会替换server_url
            self.web_url = gameOption("web_url")
            #混服部署脚本
            self.mix_deploy_script = gameOption("mix_deploy_script")
            logging.info("变量初始化完毕")
        except Exception,e1:
            self.statusCheck(False,str(e1))
        #print server_url,server_url_tag,title,server_url_tag
    def getUrl(self):
        #是否需要添加dns解析
        try:
            if not self.bigmix:
                self.yx,self.quhao = self.servername.split("_")
                domainfile = self.curdir + "/../domain_list/all_game_domain_newserver"
                special_domainfile = self.curdir + "/../domain_list/special_list"
                urlinfo = os.popen("grep '^%s@%s_' %s %s"%(self.game,self.yx,special_domainfile,domainfile)).read()
                if urlinfo.strip() == "":
                    if self.server_url == None:
                        self.statusCheck(False,"gameurl没有指定，并且在模板中也不存在")
                    if self.add_dns :
                        if self.asturl == None:
                            self.statusCheck(False,"asturl没有指定，并且在模板中也不存在")
                else:
                    # gcmob@qianqi_1@s1.gcldvn.changicvn.com@oversea@qianqi 1
                    # gcmob@feiliu_1@s1.gcmob.aoshitang.com@s1.gcmob@飞流serverid服
                    # 如果域名在模板中存在，则使用模板中的域名进行替换，否则不替换，使用传过来的变量
                    urlinfoline = urlinfo.split("\n")[0].split("@")
                    if len(urlinfoline) == 5:
                        gameurl = urlinfoline[2]
                        asturl = urlinfoline[3]
                        title = urlinfoline[4]
                        if gameurl.find("${serverid}") >= 0 :
                            self.server_url = gameurl.replace("${serverid}",self.quhao)
                        if asturl.find("${serverid}") >= 0 :
                            self.asturl = asturl.replace("${serverid}",self.quhao)
                        if title.find("${serverid}") >= 0:
                            self.title = title.replace("${serverid}",self.quhao)
                if self.server_url == None or self.server_url.strip() == "":
                    self.statusCheck(False,"获取游戏域名失败")
                if self.add_dns :
                    if self.asturl == None or self.asturl.strip() == "":
                        self.statusCheck(False,"获取ast域名失败")
                    else:
                        self.server_url_tag = self.asturl.replace(".aoshitang.com","")
                        self.ast_full_url = self.server_url_tag + ".aoshitang.com"
                        self.html.add("ast域名",self.ast_full_url)
                #游戏url
                if self.title == None or self.title.strip() == "":
                    self.title = "%s %s"%(self.yx,self.quhao)
                self.html.add("游戏域名",self.server_url)
                self.html.add("游戏标题",self.title)
                self.web_url = self.web_url.replace("${server_url}",self.server_url)
            else:
                self.web_url = self.mainserver_web_url
        except Exception,e1:
            self.statusCheck(False,str(e1))
    def cmd(self,command,msg=""):
        '''执行命令，如果返回非0则发出邮件，并退出'''
        try:
            status,stdout,stderr = self.ssh.cmd(command)
            logging.info("[%s]\n%s"%(command,stdout))
            if status != 0:
                self.html.add(command,stderr+"\n"+msg,color="red")
                logging.error("[%s]\n%s"%(command,stderr+"\n"+msg))
                self.sendEmail(False)
            else:
                return stdout
        except Exception,e1:
            self.html.add(command,str(e1)+"\n"+msg,color="red")
            logging.error("[%s]\n%s"%(command,str(e1)+"\n"+msg))
            self.sendEmail(False)
    def statusCheck(self,status,reason):
        if not status:
            self.html.add("错误描述",reason,color="red")
            logging.error(reason)
            self.sendEmail(False)
    def sendEmail(self,status):
        if not status:
            sendmail.sendmail(self.html.getCon(),self.email_address,self.mail_title + "[Fail]","deploy@game-reign.com")
            raise Exception("混服步服失败")
        else:
            sendmail.sendmail(self.html.getCon(),self.email_address,self.mail_title + "[Succ]","deploy@game-reign.com")
        logging.info("邮件已发送")
    def dnsJiexi(self):
        try:
            if self.add_dns:
                dnsSsh = ssh.ssh("10.6.196.65")
                status,stdout,stderr = dnsSsh.cmd("/app/opbin/dns/dnsapi -g %s -a add -d %s -l 1 -i %s"%(self.game,self.server_url_tag,self.dianxinIp))
                logging.info("/app/opbin/dns/dnsapi -g %s -a add -d %s -l 1 -i %s"%(self.game,self.server_url_tag,self.dianxinIp))
                logging.info(stdout)
                if stdout.find("Record add success") >= 0:
                    self.html.add("电信域名解析","成功",color="green")
                else:
                    self.html.add("电信域名解析","失败",color="red")
                if self.xianluType == 2:
                    status,stdout,stderr = dnsSsh.cmd("/app/opbin/dns/dnsapi -g %s -a add -d %s -l 2 -i %s"%(self.game,self.server_url_tag,self.liantongIp))
                    if stdout.find("Record add success") >= 0:
                        self.html.add("联通域名解析","成功",color="green")
                    else:
                        self.html.add("联通域名解析","失败",color="red")
            if self.lianyun_add_dns:
                if self.add_dns:
                    self.html.add("电信域名解析","%s CNAME %s"%(self.server_url,self.ast_full_url))
                else:
                    self.html.add("电信域名解析","%s A %s"%(self.server_url,self.dianxinIp))
                if self.xianluType == 2:
                    '''如果是CNAME记录，则电信跟联通只需要解析一条，否则需要解析每一条'''
                    if not self.add_dns:
                        self.html.add("联通域名解析","%s A %s"%(self.server_url,self.liantongIp))
        except Exception,e1:
            self.statusCheck(False,"%s\n解析域名失败"%(str(e1)))
    def getWip(self):
        '''dns解析'''
        try:
            wip = common.getServerWip(self.ip)
            logging.info("外网ip获取结果为:" + str(wip))
            if len(wip) == 0:
                self.statusCheck(False,"获取外网ip失败")
            if len(wip) >= 1:
                self.html.add("电信IP",wip[0])
                self.dianxinIp = wip[0]
                self.liantongIp = wip[0]
                self.xianluType = 1
            if len(wip) >= 2:
                self.html.add("联通IP",wip[1])
                self.liantongIp = wip[1]
                self.xianluType = 2
            if len(wip) == 1:
                self.dns_ip_name = wip[0]
            else:
                self.dns_ip_name = self.server_url
        except Exception,e1:
            self.statusCheck(False,"%s\n获取外网ip失败"%(str(e1)))
    def addBackstage(self,yx,quhao):
        errorAdd = True
        errorAddMix = True
        try:
            #添加游戏服到后台
            #status,stdout = commands.getstatusoutput("curl -s -H 'host:%s' --data 'name=%s&server_flag=%s&n_ip=%s&w_ip=%s&web_url=%s&cnc_ip=%s&startTime=%s' 'http://%s/backStage!addServer.action'"%(self.backstage_header,quhao,yx,self.ip,self.dianxinIp,self.web_url,self.liantongIp,self.starttime,self.backstage_interface_url))
            data = {}
            data["name"] = "S" + quhao
            data["server_flag"] = yx
            data["n_ip"] = self.ip
            data["w_ip"] = self.dianxinIp
            data["cnc_ip"] = self.liantongIp
            data["web_url"] = self.web_url
            data["startTime"] = self.starttime
            header = {"Host":self.backstage_header}
            url = "http://%s/backStage!addServer.action"%self.backstage_interface_url
            logging.info(str(data))
            status,stdout = urlopen(url,data=data,header=header)
            logging.info(yx + "_" + quhao + "后台接口调用结果:" + stdout)
            if status == 0:
                jsonResult = json.loads(stdout)
                statusCode = int(jsonResult["status"])
                if statusCode == 1:
                    #添加后台成功后，修改游戏服为混服
                    #status,stdout = commands.getstatusoutput("curl -H 'host:%s' --data 'master=%s_S%s&mix=%s_S%s' http://%s/backStage\!mixServer.action"%(self.backstage_header,self.mainserverYx,self.mainserverQuhao,yx,quhao,self.backstage))
                    data1 = {}
                    data1["master"] = "%s_S%s"%(self.mainserverYx,self.mainserverQuhao)
                    data1["mix"] = "%s_S%s"%(yx,quhao)
                    logging.info(str(data1))
                    url1 = "http://%s/backStage!mixServer.action"%self.backstage_interface_url
                    status,stdout = urlopen(url1,data=data1,header=header)
                    logging.info("后台混服设置结果:" + str(stdout))
                    if status == 0:
                        mixJsonResult = json.loads(stdout)
                        if int(mixJsonResult["status"]) != 1:
                            errorAddMix = False
                    else:
                        errorAddMix = False
                else:
                    errorAdd = False
                    errorAddMix = False
            else:
                return False,False
        except Exception,e1:
            logging.error("后台添加失败!"+str(e1))
            return False,False
        return errorAdd,errorAddMix
    def bigMixDeploy(self):
        zipfile = "%s_%s_properties"%(self.game,self.mainserver)
        localPropertiesDir = "%s/%s"%(self.rootDir,self.propertiesPath)
        tempDir = "%s/temp/%s"%(localPropertiesDir,zipfile)
        if os.path.exists(tempDir):
            self.statusCheck(False,"%s临时目录已经存在"%tempDir)
        #创建临时目录，将所有大混服的配置文件放在里面，打包然后上传到游戏服务器上
        os.makedirs(tempDir)
        for i in self.sList:
            yx,quhao = i.split("_")
            if not os.path.exists("%s/%s.properties"%(localPropertiesDir,yx)):
                self.statusCheck(False,"%s.properties本地不存在"%yx)
            self.cmd("test ! -f /app/%s_%s/backend/apps/%s.properties"%(self.game,self.mainserver,yx),"%s.properties在游戏服里已经存在"%yx)
            try:
                shutil.copy("%s/%s.properties"%(localPropertiesDir,yx),tempDir + "/")
            except Exception,e1:
                self.statusCheck(False,"复制%s.properties失败!err:%s"%(yx,str(e1)))
        os.chdir(localPropertiesDir + "/temp/")
        try:
            status = os.system("zip -q -r %s.zip %s"%(zipfile,zipfile))
            if status != 0 :
                self.statusCheck(False,"生成zip包失败!")
        except Exception,e1:
            self.statusCheck(False,"生成zip包失败!"+str(e1))
        try:
            self.ssh.put("%s.zip"%zipfile,remote_path="/app/%s_%s/"%(self.game,self.mainserver))
            self.ssh.put(self.curdir + "/../shell/"+self.mix_deploy_script,remote_path="/app/%s_%s/"%(self.game,self.mainserver))
        except Exception,e1:
            self.statusCheck(False,"上传zip包或者布服脚本失败!"+str(e1))
        os.system("rm -rf %s"%zipfile)
        os.system("rm -rf %s.zip"%zipfile)
        mixResult = self.cmd("cd /app/%s_%s && sh %s -m '%s_%s' -l '%s' -r '%s'"%(self.game,self.mainserver,self.mix_deploy_script,self.game,self.mainserver,self.servername,self.restart))
        logging.info(mixResult)
        if mixResult.find("backstage添加失败") >= 0:
            self.html.add("backstage添加","失败",color="red")
            self.htmlStatus = False
        self.ssh.cmd("rm -f /app/%s_%s/%s"%(self.game,self.mainserver,self.mix_deploy_script))
    def webMixDeploy(self):
        yx,num = self.servername.split("_")
        localPropertiesDir = "%s/%s"%(self.rootDir,self.propertiesPath)
        templatePath = "newserver/" + self.language + "/template"
        localTemplateDir = localPropertiesDir + "/" + templatePath
        self.cmd("test -d /app/%s_%s"%(self.game,self.mainserver),"游戏主服目录不存在")
        self.cmd("test ! -d /app/%s_%s/www_%s"%(self.game,self.mainserver,self.servername),"www_%s已经存在"%self.servername)
        #self.cmd("mkdir /app/%s_%s/www_%s"%(self.game,self.mainserver,self.servername),"创建www_%s失败"%self.servername)
        try:
            #self.ssh.put("%s/www_%s.tgz"%(templatePath,yx),remote_path="/app/%s_%s/www_%s/"%(self.game,self.mainserver,self.servername))
            #self.ssh.put(self.rootDir + "/common/nginx_template.conf",remote_path="/app/%s_%s/www_%s/"%(self.game,self.mainserver,self.servername))
            #self.ssh.put("%s/%s.properties"%(localPropertiesDir,yx),remote_path="/app/%s_%s/www_%s/"%(self.game,self.mainserver,self.servername))
            self.ssh.put(self.curdir + "/../shell/"+self.mix_deploy_script,remote_path="/app/%s_%s/"%(self.game,self.mainserver))
        except Exception,e1:
            logging.error("复制文件到服务器失败！err:\n" + str(e1))
            self.statusCheck(False,"复制文件失败！\n"+ str(e1))
        mixResult = self.cmd("cd /app/%s_%s && sh %s '%s' '%s' '%s' '%s' '%s' '%s_%s' '%s' '%s' '%s' '%s' '%s'"%(self.game,self.mainserver,self.mix_deploy_script,self.game,self.language,self.title,self.servername,self.server_url,self.game,self.mainserver,self.dns_ip_name,self.www_ip,self.www_header,self.www_port,self.restart))
        logging.info(mixResult)
        if mixResult.find("ERROR: nginx error") >= 0:
            self.html.add("nginx","nginx配置文件错误或者重启失败",color="red")
            self.htmlStatus = False
        self.ssh.cmd("rm -f /app/%s_%s/%s"%(self.game,self.mainserver,self.mix_deploy_script))
    def run(self):
        self.propertiesPath = "newserver/%s/properties"%self.language
        self.init()
        self.getWip()
        self.getUrl()
        self.cmd("test -d /app/%s_%s"%(self.game,self.mainserver),"主游戏目录不存在")
        if self.bigmix:
            self.bigMixDeploy()
        else:
            self.webMixDeploy()
        self.html.add("布服结果","成功",color="green")
        addBGError,addBGMixError = "",""
        for everyServer in self.sList:
            yx,quhao = everyServer.strip().split("_")
            if self.have_backstage_interface:
                logging.info(everyServer + "开始添加后台...")
                addBGStatus,addBGMixStatus = self.addBackstage(yx,quhao)
                if not addBGStatus:
                    addBGError += ","+yx+"_"+quhao
                    self.htmlStatus = False
                if not addBGMixStatus:
                    addBGMixError += ","+yx+"_"+quhao
                    self.htmlStatus = False
        if addBGError != "" :
            self.html.add("添加后台失败游戏服",addBGError,color="red")
        else:
            self.html.add("添加后台","成功",color="green")
        if addBGMixError != "":
            self.html.add("设置后台混服失败游戏服",addBGMixError,color="red")
        else:
            self.html.add("设置后台混服","成功",color="green")
        #非大混服查看是否需要解析域名，因为大混服主服的域名已解析，混服不需要解析
        if not self.bigmix:
            logging.info("开始dns解析...")
            self.dnsJiexi()
            logging.info("dns解析完毕!")
        tcpport = self.cmd("grep port /app/%s_%s/backend/apps/conf.xml|cut -d'>' -f2|cut -d'<' -f1"%(self.game,self.mainserver))
        self.html.add("tcp端口",tcpport)
        self.sendEmail(self.htmlStatus)
        logging.info("部署完毕!")
