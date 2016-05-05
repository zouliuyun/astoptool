#!/usr/bin/ebt python
# coding=utf8
#filename:assets_count.py
'''
  
  拉取资产信息列表
  By kuangl Create ...

'''

import os,sys,json,csv
import smtplib,shutil
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from optparse import OptionParser

#初始化信息
def init():
    global Gamerooms,Perject,fileName
    Gamerooms = options.gamerooms
    print Gamerooms
    Perject = options.perject
    print Perject
    fileName='services.csv'

def getopts():
    #MSG_USAGE='''python %s -g \'海外机房\' -p \'gcld_th\'''' % sys.argv[0]
    MSG_USAGE='''python %s -r \'海外机房\' -t \'gcld_th\'''' % sys.argv[0]
    optParser=OptionParser(MSG_USAGE)
    optParser.add_option('-r',action='store',type='string',dest='gamerooms',default='海外机房',help=u'gamerooms:海外机房')
    optParser.add_option('-t',action='store',type='string',dest='perject',default='gcld_th',help=u'perject:gcld_th,gcld_vn,gcld_kr')
    (options,args)=optParser.parse_args()
    return options

def sendmail(html,emailaddress,mailSubject,from_address="other@game-reign.com"):
        mail_list=emailaddress.split(",")
        msg=MIMEMultipart()
        msg['Accept-Language']='zh-CN'
        msg['Accept-Charset']= 'ISO-8859-1,utf-8'
        msg['From']=from_address
        msg['to']=";".join(mail_list)
        msg['Subject']=mailSubject.decode("utf-8")
        txt=MIMEText(html,'html','utf-8')
        txt.set_charset('utf-8')
        msg.attach(txt)
        file=MIMEBase('application', 'octet-stream')
        file.set_payload(open(fileName, 'rb').read())
        encoders.encode_base64(file)
        file.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(fileName))
        msg.attach(file)
        smtp=smtplib.SMTP("mail.game-reign.com")
        smtp.sendmail(msg["From"],mail_list,msg.as_string())
        smtp.close()

#接口信息
def Exec():
    #fileName=os.popen('curl -d \'action=getGame&idcname=海外机房&rackname=gcld_th\' http://op.ruizhan.com/asset/asset/inter.action 2>/dev/null').readlines()
    cmdstr = 'curl -d \'action=getGame&idcname=%s&rackname=%s\' http://op.ruizhan.com/asset/asset/inter.action 2>/dev/null'%(Gamerooms,Perject)
    datafileName=os.popen(cmdstr).readlines()
    fileName01=datafileName[0][29:][:-16]
    print fileName01
    x = json.loads(fileName01)
    print x
    fileName='services.csv'
    f = csv.writer(open("services.csv", "wb+"))
    f.writerow(["主机名", "IP", "游戏服数量", "内存", "CPU", "硬盘" , "备注"])
    for x in x:
        f.writerow([x["dno"], 
                    x["ip"], 
                    x["count"], 
                    x["men"],
                    x["cpu_num"], 
                    x["disk"], 
                    x["mark"]])

def assetrooms(gamerooms,project):
    global Gamerooms,Perject,fileName
    Gamerooms = gamerooms
    print Gamerooms
    Perject = project
    print Perject
    fileName='services.csv'
    Exec()
    cmd = 'iconv -f UTF8 -t GB18030 %s -o %s.bak && mv %s.bak %s' %(fileName,fileName,fileName,fileName)
    os.system(cmd)
    Content= 'Dear 运营: <br> &nbsp;&nbsp; 附件内是['+Gamerooms+']['+Perject+']游戏服资源使用情况文件，请查收！  <br> &nbsp;&nbsp; 如有任何问题，请及时与我联系！'
    Subject = '['+Gamerooms+']['+Perject+']服务器资源列表'
    sendmail(html=Content,emailaddress='kuangling@game-reign.com,Global-Operate@game-reign.com,opteam@game-reign.com,qinyc@game-reign.com,gufeng@game-reign.com',mailSubject=Subject)
    print "结果已通过[other@game-reign.com]账户发送邮件，请注意查收！"
    os.remove('services.csv') 
    
if __name__ == '__main__':
    if len(sys.argv)<2 and sys.argv[1] != '-h' and sys.argv[1] != '--help':
        print '''Usage:  python %s -g \'海外机房\' -p \'gcld_th\'
        python %s -h|--help''' % (sys.argv[0],sys.argv[0])
        sys.exit(1)
    options = getopts()
    init()
    Exec()
    cmd = 'iconv -f UTF8 -t GB18030 %s -o %s.bak && mv %s.bak %s' %(fileName,fileName,fileName,fileName)
    os.system(cmd)
    Content= 'Dear 运营: <br> &nbsp;&nbsp; 附件内是'+Gamerooms+'游戏服资源使用情况文件，请查收！  <br> &nbsp;&nbsp; 如有任何问题，请及时与我联系！'
    Subject = '['+Gamerooms+']['+Perject+']服务器资源列表'
    sendmail(html=Content,emailaddress='kuangling@game-reign.com,Global-Operate@game-reign.com,opteam@game-reign.com',mailSubject=Subject)
    print "结果已通过[other@game-reign.com]账户发送邮件，请注意查收！"
    os.remove('services.csv') 
