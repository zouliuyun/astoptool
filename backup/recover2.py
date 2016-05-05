#!/usr/bin/env python
#-*- coding:utf8 -*-

from arg import *
import os,json
import logging,datetime
import commands,backstage
import check,common,ssh,mailhtml,sendmail,serverlist

class recover:
    def __init__(self,game,language,servername,ip):
        '''游戏恢复任务'''
        self.game = game
        self.language = language
        self.servername = servername
        self.ip = ip
    def init(self):
        curdir = os.path.dirname(os.path.abspath(__file__))
        self.curdir = curdir
        logdir = curdir +"/../logs"
        if not os.path.exists(logdir):
            os.makedirs(logdir)
        game = self.game
        servername = self.servername
        ip = self.ip
        language = self.language
        nowstring = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        logging.basicConfig(level=logging.INFO,
                format='%(asctime)s %(levelname)s %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                filename='%s/recover_%s_%s.log'%(os.path.abspath(logdir),game,servername),
                filemode='a')
        logging.info("开始恢复游戏...")
        print "详细日志为:%s/recover_%s_%s.log"%(os.path.abspath(logdir),game,servername)
        #参数校验
        self.statusCheck(check.checkIp(ip),"ip:%s不合法"%ip)
        try:
            logging.info("%s建立ssh连接..."%ip)
            self.ssh = ssh.ssh(ip)
            logging.info("%s建立ssh连接完毕!"%ip)
            self.clientrootdir = mainOption("clientrootdir").replace("${game}",game)
            self.rootdir = mainOption("rootdir").replace("${game}",game)

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
            #下载备份sql的hadoop路径
            self.ftppath = gameOption("FTP_PATH")
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
            time_zone = gameOption("time_zone")
            self.delta_hours = 8 - int(time_zone)
            #www是老模式(www)还是新模式(www_ly_id)
            self.www_dir_type = gameOption("www_dir_type")
            #恢复脚本
            self.deploy_script = gameOption("deploy_script")
            #混服部署脚本
            self.mix_deploy_script = gameOption("mix_deploy_script")
            #执行特殊脚本
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
            logging.info("变量初始化完毕")
        except Exception,e1:
            self.statusCheck(False,str(e1))
        #print server_url,server_url_tag,title,server_url_tag
    def getUrl(self,yx,asturl,serverUrl,serverId):
        #是否需要添加dns解析
        try:
            domainfile = self.curdir + "/../domain_list/all_game_domain_newserver"
            special_domainfile = self.curdir + "/../domain_list/special_list"
            urlinfo = os.popen("grep '^%s@%s_' %s %s"%(self.game,yx,special_domainfile,domainfile)).read()
            if urlinfo.strip() == "":
                if asturl == None and serverUrl == None:
                    self.statusCheck(False,"asturl或者gameurl没有指定，并且在模板中也不存在")
            else:
                urlinfoline = urlinfo.split("\n")[0].split("@")
                if len(urlinfoline) == 5:
                    gameurl = urlinfoline[2]
                    asturl = urlinfoline[3]
                    title = urlinfoline[4]
                    if gameurl.find("${serverid}") >= 0 :
                        serverUrl = gameurl.replace("${serverid}",serverId)
                    if asturl.find("${serverid}") >= 0 :
                        asturl = asturl.replace("${serverid}",serverId)
                    if title.find("${serverid}") >= 0:
                        title = title.replace("${serverid}",serverId)
            if self.add_dns :
                if asturl == None or asturl.strip() == "":
                    self.statusCheck(False,"获取ast域名失败")
                else:
                    serverUrlTag = asturl.replace(".aoshitang.com","")
                    ast_full_url = serverUrlTag + ".aoshitang.com"
            #游戏url
            if serverUrl == None or serverUrl.strip() == "":
                self.statusCheck(False,"获取游戏域名失败")
            if title == None or title.strip() == "":
                title = "%s %s"%(yx,serverId)
            web_url = web_url.replace("${server_url}",serverUrl)
            return {"serverUrlTag":serverUrlTag,"serverUrl":serverUrl,"asturl":asturl,"title":title}
        except Exception,e1:
            self.statusCheck(False,str(e1))
    def cmd(self,command,msg=""):
        '''执行命令，如果返回非0则发出邮件，并退出'''
        try:
            status,stdout,stderr = self.ssh.cmd(command)
            logging.info("[%s]\n%s"%(command,stdout))
            if status != 0:
                logging.error("[%s]\n%s"%(command,stderr+"\n"+msg))
                return ""
                #sys.exit(1) 
            else:
                return stdout
        except Exception,e1:
            logging.error("[%s]\n%s"%(command,str(e1)+"\n"+msg))
            return ""
            #sys.exit(1)
    def statusCheck(self,status,reason):
        if not status:
            logging.error(reason)
            #sys.exit(1)
#    def sendEmail(self,status):
#        if not status:
#            sendmail.sendmail(self.html.getCon(),self.email_address,self.mail_title + "[Fail]","deploy@game-reign.com")
#        else:
#            sendmail.sendmail(self.html.getCon(),self.email_address,self.mail_title + "[Succ]","deploy@game-reign.com")
#        logging.info("邮件已发送")
    def dnsJiexi(self,server_url_tag,serverUrl):
        try:
            if self.add_dns:
                dnsSsh = ssh.ssh("10.6.196.65")
                status,stdout,stderr = dnsSsh.cmd("/app/opbin/dns/dnsapi -g %s -a up -d %s -l 1 -i %s"%(self.game,server_url_tag,self.dianxinIp))
                logging.info("/app/opbin/dns/dnsapi -g %s -a up -d %s -l 1 -i %s"%(self.game,server_url_tag,self.dianxinIp))
                logging.info(stdout)
                if stdout.find("Record modify success") >= 0:
                    logging.info("电信域名解析修改成功")
                else:
                    logging.info("电信域名解析修改失败")
                if self.xianluType == 2:
                    status,stdout,stderr = dnsSsh.cmd("/app/opbin/dns/dnsapi -g %s -a up -d %s -l 2 -i %s"%(self.game,self.server_url_tag,self.liantongIp))
                    logging.info("/app/opbin/dns/dnsapi -g %s -a up -d %s -l 2 -i %s"%(self.game,self.server_url_tag,self.liantongIp))
                    logging.info(stdout)
                    if stdout.find("Record modify success") >= 0:
                        logging.info("联通域名解析修改成功")
                    else:
                        logging.info("联通域名解析修改失败")
            if self.lianyun_add_dns:
                if self.add_dns:
                    logging.info("服务器恢复不用通知联运cname解析，我们自己已解析！")
                else:
                    logging.info("服务器恢复需要通知联运重新做A记录%s A %s" %(serverUrl,self.dianxinIp))
                if self.xianluType == 2:
                    '''如果是CNAME记录，则电信跟联通只需要解析一条，否则需要解析每一条'''
                    if not self.add_dns:
                        logging.info("联通域名解析","%s A %s"%(serverUrl,self.liantongIp))
        except Exception,e1:
            #self.statusCheck(False,"%s\n解析域名失败"%(str(e1)))
            logging.info("%s\n解析域名失败"%(str(e1)))
    def getWip(self):
        '''dns解析'''
        try:
            wip = common.getServerWip(self.ip)
            logging.info("外网ip获取结果为:" + str(wip))
            if len(wip) == 0:
                self.statusCheck(False,"获取外网ip失败")
            if len(wip) >= 1:
                self.dianxinIp = wip[0]
                self.liantongIp = wip[0]
                self.xianluType = 1
            if len(wip) >= 2:
                self.liantongIp = wip[1]
                self.xianluType = 2
            #if len(wip) == 1:
            #    self.dns_ip_name = wip[0]
            #else:
            #    self.dns_ip_name = self.server_url
        except Exception,e1:
            self.statusCheck(False,"%s\n获取外网ip失败"%(str(e1)))
    def modifyBackstage(self):
        header = {"host":self.backstage_header}
        data = {}
        data["servername"] = "%s_S%s"%(self.yx,self.quhao)
        data["n_ip"] = self.ip
        data["w_ip"] = self.dianxinIp
        data["cnc_ip"] = self.liantongIp
        result = backstage.upBackstage(self.backstage_interface_url,data,header)
        if result["status"]:
            print "后台修改成功！"
        else:
            print "后台修改失败！" + result["msg"]
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
                        mixserver = deployMix.deploy(self.game,self.language,big_mix_list,self.servername,"yes",None,None,None,False)
                        mixserver.run()
                        self.html.add("大混服部署","成功,请注意混服邮件！",color="green")
                    except Exception,e2:
                        self.html.add("大混服部署",str(e2),color="red")
                        self.htmlStatus = False
            except Exception,e1:
                self.html.add("大混服部署","获取大混服参数错误",color="red")
                self.htmlStatus = False
        pass
    def recoverServers(self):
        serverList = serverlist.getRecoverServerList(self.backstage_db,self.backstage_tag,self.partnersType,self.backstage,self.servername)
        MainServers=[]
        MixServers=[]
        for server in serverList:
            if serverList[server]['mixflag'] == 1:
                MainServers.append(serverList[server])
            elif not self.big_mix_server:
                MixServers.append(serverList[server])
        for serverflag in MainServers:
            deploy_common_script = "deploy_common.sh"
            self.servername=serverflag['MainName']
            self.starttime=serverflag['starttime']
            self.cleartime = (datetime.datetime.strptime(self.starttime,"%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=self.delta_hours) - datetime.timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
            self.yx,self.quhao = self.servername.split("_")
            self.getUrl()
            newserver_parameter = " '%s' '%s' '%s'  '%s'  '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s'"%(self.game,self.language,self.servername,self.title,self.server_url,self.dns_ip_name,self.is_mobile,self.cleartime,self.innit_sql,self.www_dir_type,self.www_ip,self.www_port,self.www_header,self.clear_script,self.template_tar_dir,self.template_exclude_dir,'recover',self.ftppath,self.deploy_special_script,self.deploy_script)
            self.cmd("test ! -d /app/%s_%s"%(self.game,self.servername),"游戏目录已经存在")
            self.cmd("test ! -e /app/nginx/conf/vhost/%s_%s.conf"%(self.game,self.servername),"nginx配置文件已存在")
            self.cmd("if [ $(pandora -e 'show databases' | grep -E '%s_%s$'|wc -l) != 0 ];then exit 1; fi"%(self.game,self.servername),"数据库已经存在")
            #self.cmd("mkdir /app/%s_%s"%(self.game,self.servername),"创建游戏目录失败")
            self.cmd("[ -d %s/shell ] || mkdir -p  %s/shell"%(self.clientrootdir,self.clientrootdir))
            try:
                self.ssh.put("%s/../shell/%s"%(self.curdir,deploy_common_script),remote_path=self.clientrootdir+"/shell")
                self.ssh.put("%s/../shell/%s"%(self.curdir,self.deploy_script),remote_path=self.clientrootdir+"/shell")
                self.ssh.put("%s/../shell/%s"%(self.curdir,self.clear_script),remote_path=self.clientrootdir+"/shell")
                if self.deploy_special_script.strip() != "":
                    self.ssh.put("%s/../shell/%s"%(self.curdir,self.deploy_special_script),remote_path=self.clientrootdir+"/shell")
            except Exception,e1:
                self.statusCheck(False,str(e1)+"\nscp %s %s %s到服务器失败"%(self.deploy_script,self.clear_script,deploy_common_script))
            print newserver_parameter
            try:
                recover_stdout = self.cmd("source /etc/profile && sh %s/shell/%s %s"%(self.clientrootdir,deploy_common_script,newserver_parameter), msg="部署服务器失败!")
                if recover_stdout.find("backstage添加失败") >= 0:
                    logging.info("后台agent配置添加失败")
                if recover_stdout.find("logcheck添加失败") >= 0:
                    logging.info("logcheck添加失败")
                if recover_stdout.find("nginx error") >= 0:
                    logging.info("nginx 配置问题，请查看！")
                logging.info("开始修改主服后台...")
                #self.modifyBackstage()
                logging.info("后台修改完毕!")
                logging.info("开始修改dns解析...")
                #self.dnsJiexi()
                logging.info("dns解析修改完毕!")
                self.bigMixServerDeploy()
            except Exception,e5:
                print "[%s] 还原异常:%s"%(serverflag,str(e5))
        for mix_serverflag in MixServers:
            self.mainserver=mix_serverflag['MainName']
            self.servername=mix_serverflag['servername']
            deployCommonScript = "deploy_mix_common.sh"
            self.yx,self.quhao = self.servername.split("_")
            self.restart='yes'
            self.getUrl()
            self.cmd("test -d /app/%s_%s"%(self.game,self.mainserver),"游戏主服目录不存在")
            self.cmd("test ! -d /app/%s_%s/www_%s"%(self.game,self.mainserver,self.servername),"www_%s已经存在"%self.servername)
            try:
                self.ssh.put("%s/../shell/%s"%(self.curdir,self.mix_deploy_script),remote_path=self.clientrootdir+"/shell")
                self.ssh.put("%s/../shell/%s"%(self.curdir,deployCommonScript),remote_path=self.clientrootdir+"/shell")
            except Exception,e1:
                self.statusCheck(False,str(e1)+"\nscp %s %s 到服务器失败"%(self.mix_deploy_script,deployCommonScript))
            mixserver_parameter = " '%s' '%s' '%s'  '%s'  '%s' '%s_%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s'"%(self.game,self.language,self.title,self.servername,self.server_url,self.game,self.mainserver,self.dns_ip_name,self.www_ip,self.www_header,self.www_port,self.restart,self.mix_deploy_script,self.deploy_special_script)
            print mixserver_parameter
            recover_mix_stdout = self.cmd("source /etc/profile && sh %s/shell/%s %s"%(self.clientrootdir,deployCommonScript,mixserver_parameter), msg="恢复混服服务器失败!")
            logging.info(recover_mix_stdout)
            #self.modifyBackstage()
            #self.dnsJiexi()
    def run(self):
        self.init()
        ###self.getUrl()
        self.getWip()
        self.recoverServers()
