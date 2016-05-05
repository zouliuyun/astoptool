#!/usr/bin/env python
#-*- coding:utf8 -*-

from arg import *
import os,json,sys,urllib
import logging,datetime
import commands
import check,common,ssh,mailhtml,sendmail,serverlist,backstage,getip

class deploy:
    def __init__(self,game,language,servername,ip,cleartime,title,gameurl,asturl,skipcheck):
        '''游戏部署任务'''
        self.game = game
        self.language = language
        self.servername = servername
        self.cleartime = cleartime
        self.ip = ip
        self.title = title
        self.server_url = gameurl
        self.asturl = asturl
        self.skipcheck = skipcheck
    def init(self):
        curdir = os.path.dirname(os.path.abspath(__file__))
        self.curdir = curdir
        logdir = curdir +"/../logs"
        if not os.path.exists(logdir):
            os.makedirs(logdir)
        game = self.game
        servername = self.servername
        ip = self.ip
        cleartime = self.cleartime
        language = self.language
        nowstring = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        logging.basicConfig(level=logging.INFO,
                format='%(asctime)s %(levelname)s %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                #filename='%s/deploy_%s_%s_%s.log'%(os.path.abspath(logdir),game,servername,nowstring),
                #filename='%s/deploy_%s_%s.log'%(os.path.abspath(logdir),game,servername),
                #filemode='a'
                )
        logging.info("开始部署游戏...")
        print "详细日志为:%s/deploy_%s_%s.log"%(os.path.abspath(logdir),game,servername)
        sys.stdout.flush()
        self.html = mailhtml.mailhtml("%s_%s_deploy.html"%(game,servername),"%s_%s游戏服部署"%(game,servername))
        self.email_address = gameOption("email_address")
        self.mail_title = "[%s][%s]游戏服部署"%(game,servername)
        #参数校验
        self.yx,self.quhao = self.servername.split("_")
        self.statusCheck(check.checkIp(ip),"ip:%s不合法"%ip)
        self.html.add("服务器ip",ip)
        self.statusCheck(check.checkServer(servername),"游戏名称:%s 不合法"%servername)
        self.html.add("游戏名称",servername)
        self.statusCheck(check.checkDatetime(cleartime),"清档时间:%s 不合法"%cleartime)
        self.htmlStatus = True
        try:
            logging.info("%s建立ssh连接..."%ip)
            self.ssh = ssh.ssh(ip)
            logging.info("%s建立ssh连接完毕!"%ip)
            self.clientrootdir = mainOption("clientrootdir").replace("${game}",game)
            self.rootdir = mainOption("rootdir").replace("${game}",game)

            #后台相关信息
            self.backstage = gameOption("backstage")
            self.backstage_db = gameOption("backstage_db")
            self.backstage_tag = gameOption("backstage_tag",default="")
            self.backstage_interface_url = gameOption("backstage_interface_url")
            self.backstage_header = gameOption("backstage_header")
            self.have_backstage_interface = gameOption("have_backstage_interface",type="bool")
            #游戏服务器需要下载资源的地址信息
            self.www_ip = gameOption("www_ip")
            self.www_port = gameOption("www_port",default="80")
            self.www_header = gameOption("www_header")
            #是否为海外
            self.is_oversea = gameOption("is_oversea",type="bool")
            #是否为手游
            if gameOption("is_mobile",type="bool"):
                self.is_mobile = "mobile"
                self.partnersType = 2
            else:
                self.is_mobile = "web"
                self.partnersType = 1
            #建库sql
            self.innit_sql = self.game + "_"+ self.language+"_init" + ".sql"
            #判断是否检查游戏服存在与否，主要用于没有后台时的布服
            if not self.skipcheck:
                serverExistsJson = serverlist.serverExists(self.backstage_db,self.backstage_tag,self.partnersType,servername,self.backstage)
                if serverExistsJson["result"]:
                    self.statusCheck(False,"游戏已经存在，请确认")
            self.time_zone = gameOption("time_zone",default="+8")
            delta_hours = 8 - int(self.time_zone)
            self.starttime = (datetime.datetime.strptime(cleartime,"%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=delta_hours) + datetime.timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
            self.html.add("开服时间(北京+8区)",self.starttime)
            self.html.add("清档时间(服务器%s区)"%self.time_zone,cleartime)
            #www是老模式(www)还是新模式(www_ly_id)
            self.www_dir_type = gameOption("www_dir_type",default="new")
            #布服脚本
            self.deploy_script = gameOption("deploy_script")
            #布服特殊脚本
            self.deploy_special_script = gameOption("deploy_special_script")
            #清档脚本
            self.clear_script = gameOption("clear_script")
            #是否添加ast域名解析
            self.add_dns = gameOption("add_dns",type="bool")
            #是否需要联运解析域名
            self.lianyun_add_dns = gameOption("lianyun_add_dns",type="bool")
            #后台游戏域名，后续会替换server_url
            self.web_url = gameOption("web_url")
            #布服公共包目录
            self.template_tar_dir = gameOption("template_tar_dir")
            self.template_exclude_dir = gameOption("template_exclude_dir")
            #是否需要部署大混服
            self.big_mix_server = gameOption("big_mix_server",type="bool")
            #dns解析使用的game
            self.dns_game = gameOption("dns_game",default=self.game)
            logging.info("变量初始化完毕")
        except Exception,e1:
            self.statusCheck(False,str(e1))
        #print server_url,server_url_tag,title,server_url_tag
    def getUrl(self):
        #是否需要添加dns解析
        try:
            domainfile = self.curdir + "/../domain_list/all_game_domain_newserver"
            if check.nullCheck(self.server_url) or check.nullCheck(self.title):
                special_domainfile = self.curdir + "/../domain_list/special_list"
                urlinfo = os.popen("grep '^%s@%s_' %s %s"%(self.game,self.yx,special_domainfile,domainfile)).read()
                print "urlinfo str:",urlinfo
                if urlinfo.strip() == "":
                    #if self.asturl == None and self.server_url == None:
                    if check.nullCheck(self.asturl) and check.nullCheck(self.server_url):
                        self.statusCheck(False,"asturl或者gameurl没有指定，并且在模板中也不存在")
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
                            if check.nullCheck(self.title):
                                self.title = title.replace("${serverid}",self.quhao)
            if self.add_dns :
                #if self.asturl == None or self.asturl.strip() == "":
                if check.nullCheck(self.asturl):
                    self.statusCheck(False,"获取ast域名失败")
                else:
                    self.server_url_tag = self.asturl.replace(".aoshitang.com","")
                    self.ast_full_url = self.server_url_tag + ".aoshitang.com"
                    self.html.add("ast域名",self.ast_full_url)
            #游戏url
            #if self.server_url == None or self.server_url.strip() == "":
            if check.nullCheck(self.server_url):
                self.statusCheck(False,"获取游戏域名失败")
            #if self.title == None or self.title.strip() == "":
            if check.nullCheck(self.title):
                self.title = "%s %s"%(self.yx,self.quhao)
            self.html.add("游戏域名",self.server_url)
            self.html.add("游戏标题",self.title)
            self.web_url = self.web_url.replace("${server_url}",self.server_url)
        except Exception,e1:
            self.statusCheck(False,str(e1))
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
    def sendEmail(self,status):
        if not status:
            sendmail.sendmail(self.html.getCon(),self.email_address,self.mail_title + "[Fail]","NEWSERVER@game-reign.com")
        else:
            sendmail.sendmail(self.html.getCon(),self.email_address,self.mail_title + "[Succ]","NEWSERVER@game-reign.com")
        logging.info("邮件已发送")
    def dnsJiexi(self):
        try:
            if self.add_dns:
                dnsSsh = ssh.ssh("10.6.196.65")
                logging.info("/app/opbin/dns/dnsapi -g %s -a add -d %s -l 1 -i %s"%(self.dns_game,self.server_url_tag,self.dianxinIp))
                status,stdout,stderr = dnsSsh.cmd("/app/opbin/dns/dnsapi -g %s -a add -d %s -l 1 -i %s"%(self.dns_game,self.server_url_tag,self.dianxinIp))
                logging.info(stdout)
                if stdout.find("Record add success") >= 0:
                    self.html.add("电信域名解析","成功",color="green")
                else:
                    self.html.add("电信域名解析","失败!" + stdout.strip(),color="red")
                    self.htmlStatus = False
                    logging.info(str(stderr))
                if self.xianluType == 2:
                    logging.info("/app/opbin/dns/dnsapi -g %s -a add -d %s -l 2 -i %s"%(self.dns_game,self.server_url_tag,self.liantongIp))
                    status,stdout,stderr = dnsSsh.cmd("/app/opbin/dns/dnsapi -g %s -a add -d %s -l 2 -i %s"%(self.dns_game,self.server_url_tag,self.liantongIp))
                    logging.info(stdout)
                    if stdout.find("Record add success") >= 0:
                        self.html.add("联通域名解析","成功",color="green")
                    else:
                        self.html.add("联通域名解析","失败!"+stdout.strip(),color="red")
                        self.htmlStatus = False
                        logging.info(str(stderr))
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
            wip = getip.getServerWip(self.ip)
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
    def addBackstage(self):
        try:
            data = {}
            data["name"] = "S%s"%self.quhao
            data["server_flag"] = self.yx
            data["n_ip"] = self.ip
            data["w_ip"] = self.dianxinIp
            data["web_url"] = self.web_url
            data["cnc_ip"] = self.liantongIp
            data["startTime"] = self.starttime
            data["time_zone"] = int(self.time_zone)
            header = {"Host":self.backstage_header}
            logging.info("后台信息:%s"%str(data))
            logging.info(urllib.urlencode(data))
            result = backstage.addBackstage(self.backstage_interface_url,data,header)
            logging.info("后台接口调用结果:" + str(result["response"]))
            if result["status"]:
                self.html.add("后台添加","成功",color="green")
            else:
                self.html.add("后台添加",result["msg"],color="red")
                self.htmlStatus = False
        except Exception,e1:
            self.html.add("后台添加",str(e1),color="red")
            self.htmlStatus = False
    def bigMixServerDeploy(self):
        if self.big_mix_server:
            big_mix_list = ""
            big_mix_list_exclude = ""
            try:
                big_mix_list = gameOption("big_mix_list")
                # 如果混服列表为空，则到后台数据库查询混服列表
                if not big_mix_list:
                    big_mix_list_exclude = gameOption("big_mix_list_exclude")
                    big_mix_list = serverlist.getMixServer(self.backstage_db,self.backstage_tag,self.partnersType,self.backstage,big_mix_list_exclude)
                if not big_mix_list or big_mix_list.strip() == "":
                    self.html.add("大混服部署","混服列表为空",color="red")
                    self.htmlStatus = False
                else:
                    import deployMix
                    try:
                        mixserverlist = [ "%s_%s"%(i.strip(),self.quhao) for i in big_mix_list.split(",") ]
                        #mixserverlist.remove(self.servername.strip())
                        mixserverlistStr = ",".join(mixserverlist)
                        logging.info("大混服列表为:%s"%mixserverlistStr)
                        mixserver = deployMix.deploy(self.game,self.language,mixserverlistStr,self.servername,"yes",None,None,None,False)
                        mixserver.run()
                        self.html.add("大混服部署","成功,请注意混服邮件！",color="green")
                    except Exception,e2:
                        self.html.add("大混服部署",str(e2),color="red")
                        self.htmlStatus = False
            except Exception,e1:
                self.html.add("大混服部署","获取大混服参数错误",color="red")
                self.htmlStatus = False
        pass
    def mobile_entrance_control(self):
        try:
            from bible.mobile_entrance import MobileEntrance
            mobile_entrance = MobileEntrance(self.game, self.language, self.yx, self.quhao)
            ret_value = mobile_entrance.add(self.server_url, self.dianxinIp, self.tcpport.strip('\n'))
            if ret_value:
                self.html.add("手游入口信息", "成功", color="green")
            else:
                self.html.add("手游入口信息", "未自动添加，请运营手动添加:%s" % ret_value, color="red")

        except Exception, e:
            self.html.add("手游入口信息", str(e) ,color="red")
            self.htmlStatus = False

    def run(self):
        self.init()
        self.getUrl()
        self.getWip()
        self.cmd("test ! -d /app/%s_%s"%(self.game,self.servername),"游戏目录已经存在")
        self.cmd("test ! -e /app/nginx/conf/vhost/%s_%s.conf"%(self.game,self.servername),"nginx配置文件已存在")
        self.cmd("if [ $(pandora -e 'show databases' | grep -E '%s_%s$'|wc -l) != 0 ];then exit 1; fi"%(self.game,self.servername),"数据库已经存在")
        #self.cmd("mkdir /app/%s_%s"%(self.game,self.servername),"创建游戏目录失败")
        self.cmd("[ -d %s/shell ] || mkdir -p  %s/shell"%(self.clientrootdir,self.clientrootdir))
        deploy_common_script = "deploy_common.sh"
        try:
            self.ssh.put("%s/../shell/%s"%(self.curdir,self.deploy_script),remote_path=self.clientrootdir+"/shell")
            self.ssh.put("%s/../shell/%s"%(self.curdir,self.clear_script),remote_path=self.clientrootdir+"/shell")
            self.ssh.put("%s/../shell/%s"%(self.curdir,deploy_common_script),remote_path=self.clientrootdir+"/shell")
            if self.deploy_special_script.strip() != "":
                self.ssh.put("%s/../shell/%s"%(self.curdir,self.deploy_special_script),remote_path=self.clientrootdir+"/shell")
        except Exception,e1:
            self.statusCheck(False,str(e1)+"\nscp %s %s到服务器失败"%(self.deploy_script,self.clear_script))
        newserver_parameter = " '%s' '%s' '%s'  '%s'  '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s'"%(self.game,self.language,self.servername,self.title,self.server_url,self.dns_ip_name,self.is_mobile,self.cleartime,self.innit_sql,self.www_dir_type,self.www_ip,self.www_port,self.www_header,self.clear_script,self.template_tar_dir,self.template_exclude_dir,'new','',self.deploy_special_script,self.deploy_script)
        deploy_stdout = self.cmd("source /etc/profile && sh %s/shell/%s %s"%(self.clientrootdir,deploy_common_script,newserver_parameter), msg="部署服务器失败!")
        self.html.add("布服结果","成功",color="green")
        #self.cmd("rm -f /app/%s_%s/%s"%(self.game,self.servername,self.deploy_script))
        if deploy_stdout.find("backstage添加失败") >= 0:
            self.html.add("backstage配置","失败",color="red")
            self.htmlStatus = False
        if deploy_stdout.find("logcheck添加失败") >= 0:
            self.html.add("logcheck配置","失败",color="red")
            self.htmlStatus = False
        if deploy_stdout.find("nginx error") >= 0:
            self.html.add("nginx配置","错误",color="red")
            self.htmlStatus = False
        if self.have_backstage_interface:
            logging.info("开始添加后台...")
            self.addBackstage()
            logging.info("后台添加完毕!")
        logging.info("开始dns解析...")
        self.dnsJiexi()
        logging.info("dns解析完毕!")
        self.tcpport = self.cmd("grep port /app/%s_%s/backend/apps/conf.xml|cut -d'>' -f2|cut -d'<' -f1"%(self.game,self.servername))
        self.html.add("tcp端口", self.tcpport)
        self.bigMixServerDeploy()

        if self.is_mobile == 'mobile':
            logging.info("开始添加手游入口信息...")
            self.mobile_entrance_control()

        self.sendEmail(self.htmlStatus)
        logging.info("部署完毕!")
