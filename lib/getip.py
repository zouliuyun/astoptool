#!/usr/bin/env python
#-*- coding:utf8 -*-
import re
import ssh,check
import mysql,arg
def getServerWip(interIp):
    get_outip_from_zichan = arg.gameOption("get_outip_from_zichan",type="bool",default=False)
    iplist = []
    if not get_outip_from_zichan:
        sshobj = ssh.ssh(interIp.strip())
        cmd = "/sbin/ifconfig -a | grep 'inet addr'|cut -d':' -f2|cut -d' ' -f1"
        status,r,stderr = sshobj.cmd(cmd)
        if status == 0:
            for ip in r.split("\n"):
                if re.search(r"^(10\.|192\.168|172\.1[6-9]\.|172\.2[0-9]\.|172\.3[01]\.|169\.254\.|127\.)",ip) or ip.strip() == "":
                    continue
                else:
                    iplist.append(ip.strip())
            if len(iplist) == 0:
                #status,r1,stderr = sshobj.cmd("curl -s ip.cn | awk '{print $2}' | sed 's/[^0-9\\.]*\\(.*\\)/\\1/g'")
                status,r1,stderr = sshobj.cmd("curl -s ipip.net | awk '{print $2}' | sed 's/[^0-9\\.]*\\(.*\\)/\\1/g'")
                if check.checkIp(r1) :
                    iplist.append(r1.strip())
        else:
            print "[%s] out:%serr:%s"%(cmd,out,err)
    else:
        hsot = arg.mainOption("zichan_host")
        user = arg.mainOption("zichan_user")
        pwd = arg.mainOption("zichan_pwd")
        port = arg.mainOption("zichan_port",type="int")
        db = arg.mainOption("zichan_db")
        my = mysql.mysql(hsot,user,pwd,db,port)
        mylist = my.query("select asset_outip.ip,isp from asset_inip join asset_outip on asset_outip.did = asset_inip.did and asset_inip.ip = '%s'"%interIp)
        for i in mylist:
            if i[1].strip() == "电信":
                iplist.insert(0,i[0].strip())
            else:
                iplist.append(i[0].strip())
        pass
    return iplist
if __name__ == "__main__":
    import state
    state.game = "tjxs"
    state.language = "cn"
    print getServerWip("183.131.76.38")
