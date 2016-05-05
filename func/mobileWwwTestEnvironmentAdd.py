#!/usr/bin/env python
#-*- coding:utf8 -*-
import optparse
import sys,datetime,os,re
import state,ssh,arg
 
def addWhiteIp(wwwIp,wwwPort,ipList):    
    file = "/app/nginx/conf/whitelist/%s_%s_whitelist.conf"%(state.game,state.language)    
    basename = os.path.basename(file)
    bakdir = "/app/opbak/nginxconf/"
    curtime=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backfile="%s_%s"%(basename,curtime)
    if ipList == '' or not ipList:
        print "需要添加的白名单ip为空，请确认！"
        sys.exit(1)
    wwwIpSshAstd = ssh.ssh(wwwIp,wwwPort)
    #wwwIpSshRoot = ssh.ssh(wwwIp,wwwPort,user="root")
    wwwIpSshAstd.exitcmd("mkdir -p %s"%bakdir)
    wwwIpSshAstd.exitcmd("cp %s %s/%s"%(file,bakdir,backfile))
    ipList = ipList.split(',')
    wwwForward = arg.gameOption("mobile_www_forward",type="bool",default=False)
    if wwwForward:
        remoteTag = "http_x_forwarded_for"
    else:
        remoteTag = "remote_addr"
    for whiteIp in ipList:
        content = '''
if ( $%s = %s ) {
        set $gototest 1;
}'''%(remoteTag,whiteIp)
        wwwIpSshAstd.exitcmd("echo  '%s' >> %s"%(content,file))
        wwwIpSshAstd.exitcmd("sed -i '/^$'/d %s"%file)
    #out = wwwIpSshRoot.exitcmd("/app/nginx/sbin/nginx -t 2>&1")
    out = wwwIpSshAstd.exitcmd("sudo /app/nginx/sbin/nginx -t 2>&1")
    if not re.search("nginx: the configuration file (/app/nginx/|/usr/local/nginx/)conf/nginx.conf syntax is ok",out) or not re.search("nginx: configuration file (/app/nginx/|/usr/local/nginx/)conf/nginx.conf test is successful",out):
        print "nginx语法错误"
        print out
        wwwIpSshAstd.exitcmd("cp %s/%s %s"%(bakdir,backfile,file))
    else:
        #wwwIpSshRoot.exitcmd("/app/nginx/sbin/nginx -s reload")
        wwwIpSshAstd.exitcmd("sudo /app/nginx/sbin/nginx -s reload")
        print "添加白名单完成"
        result=wwwIpSshAstd.exitcmd("grep 'if' %s | awk -F '[=)]' '{print $2}'"%file)
        print "已有白名单ip如下：\n%s"%result

def mobileWwwTestEnvironmentAdd(ip):
    wwwIp = arg.gameOption("mobile_www_ip")
    wwwBackupIp = arg.gameOption("mobile_www_backup_ip",default="")
    wwwPort = arg.gameOption("mobile_www_port", default=22)
    if wwwBackupIp != "":
        addWhiteIp(wwwIp,wwwPort,ip)
        addWhiteIp(wwwBackupIp,wwwPort,ip)
    else:
        addWhiteIp(wwwIp,wwwPort,ip)
