#!/usr/bin/env python
# encoding=utf8
import os
import sys
import MySQLdb
import time
import ConfigParser
import smtplib
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from optparse import OptionParser
def init():
    global KfIp
    global bsDb
    global bsdbHost
    global pwd
    global preDb
    global KfdbName
    global KingNum
    global addNum
    global IncludeYxs
    global ExcludeYxs
    global Emailaddress
    config = ConfigParser.ConfigParser()
    dir = os.path.dirname(os.path.abspath(__file__))
    filepath = "%s/gcld_kfgz.conf" % dir
    if not os.path.exists(filepath):
        raise Exception("ERROR: "+options.game+".conf该配置文件不存在！")
    config.read(filepath)
    configTag=options.game+'_'+options.language
    try:
        KfIp = config.get(configTag,"gwip")
        bsDb = config.get(configTag,"backstage_db")
        bsdbHost = config.get(configTag,"bsdb_host")
        pwd = config.get(configTag,"passwd")
        preDb = config.get(configTag,"predb")
        KfdbName = config.get(configTag,"kfdbname")
        KingNum = config.get(configTag,"kingnum")
        IncludeYxs = config.get(configTag,"includeyxs")
        ExcludeYxs = config.get(configTag,"excludeyxs")
        Emailaddress = config.get(configTag,"email_address")
    except Exception,e1:
        print "Error:game:%s:,language:%s not config" % (options.game,options.language)
        sys.exit(1)
    if 0 < int(KingNum) < 4:
        addNum=2
    elif 4 <= int(KingNum) < 12:
        addNum=4
    elif 12 <= int(KingNum) < 36:
        addNum=6
    elif 36 <= int(KingNum):
        addNum=10
	
def sendEmail(fileName,bodyName):
    mail_list=Emailaddress.split(',')
    #mail_list.append('tech-op@game-reign.com')
    msg=MIMEMultipart()
    msg['Accept-Language']='zh-CN'
    msg['Accept-Charset']= 'ISO-8859-1,utf-8'
    msg['From']="op-help@game-reign.com"
    msg['to']=";".join(mail_list)
    msg['Subject']=u'['+options.game+']['+ options.language  +'][kfgz row match]['+time.strftime('%Y-%m-%d %H:%M',time.localtime())+']'
    txt=MIMEText(open(bodyName).read().replace('\n','<br>'),'html','utf-8')
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
def mysql_bsconnect(sql,host,db_name):
    try:
        conn=MySQLdb.connect(host=host,user='rd',passwd=pwd,db=db_name,port=3306)
        cur=conn.cursor()
        cur.execute(sql)
        result=cur.fetchall()
        cur.close()
        conn.close()
        return result
    except MySQLdb.Error,e:
        print "Mysql Error %d: %s" % (e.args[0],e.args[1])

def getopts():
    MSG_USAGE='''python %s -g gcld -L cn -l80 -n7 -d"2014-07-20 00:00:00" -H"2014-07-15 00:00:00"''' % sys.argv[0]
    optParser=OptionParser(MSG_USAGE)
    optParser.add_option('-g',action='store',type='string',dest='game',default='gcld',help=u'攻城系列的具体项目，如：gcld，gchw，gcmob')
    optParser.add_option('-L',action='store',type='string',dest='language',default='cn',help=u'项目下的具体语言，如：cn/tc/tw')
    optParser.add_option('-l',action='store',type='string',dest='lv',default='70',help=u'查询大于等于参数等级的玩家信息')
    optParser.add_option('-n',action='store',type='string',dest='days',default='3',help=u'查询小于等于n天登陆过的玩家信息')
    optParser.add_option('-d',action='store',type='string',dest='KF_DATE',default='',help=u'查询范围截止日期，默认为截止到今天开的游戏服')
    optParser.add_option('-H',action='store',type='string',dest='HF_DATE',default='',help=u'上一次跨服国战的结束日期，用于拉去期间的合服列表')
    (options,args)=optParser.parse_args()
    return options

def getAliveOpenServers():
    #SQL='select concat(server_flag, \'_\', name), startTime, w_ip from server where status=9 and mixflag = 1 and date(startTime) < \''+ options.KF_DATE +'\' and istest = 0;'
    whereStr=""
    if IncludeYxs:
        tmp=[]
        for s in IncludeYxs.strip().split(","):
            tmp.append(s)
        for i in (range(len(tmp))):
            if i==0:
                whereStr += ' and (server_flag="%s"' %tmp[i]
            else:
                whereStr += ' or server_flag="%s"' %tmp[i]
        whereStr += ")"
    if ExcludeYxs:
        tmp=[]
        for s in ExcludeYxs.strip().split(","):
            tmp.append(s)
        for i in (range(len(tmp))):
                whereStr += ' and server_flag!="%s"' %tmp[i]
    if not whereStr:
        SQL='select concat(server_flag, \'_\', name), startTime, w_ip from server where status=9 and mixflag = 1 and date(startTime) < \''+ options.KF_DATE +'\' and istest = 0;'
    else:
        SQL='select concat(server_flag, \'_\', name), startTime, w_ip from server where status=9 and mixflag = 1 '+ whereStr + ' and date(startTime) < \''+ options.KF_DATE +'\' and istest = 0;'
    #print SQL
    serverlist=[]
    server_result=mysql_bsconnect(sql=SQL,host=bsdbHost,db_name=bsDb)
    for result in server_result:
        serverlist.append([result[0],result[1].strftime('%Y-%m-%d %H:%M:%S'),result[2]])
    lv_sql='select  if (b.count is null, 0, count), a.force_id, a.force_lv from force_info a left join ( select count(1) count, force_id from player where date(login_time) >= date_sub(now(), interval '+ options.days +' day) and player_lv >= '+ options.lv +' group by force_id ) b on b.force_id = a.force_id;'
    for i in range(len(serverlist)):
        server_info=[]
        ip=serverlist[i][2]
        dbname=preDb+'_'+serverlist[i][0].replace('S','')
        server_info=mysql_bsconnect(sql=lv_sql,host=ip,db_name=dbname)
        serverlist.append(serverlist[i]+list(server_info[1]))
        serverlist.append(serverlist[i]+list(server_info[2]))
        serverlist[i]=serverlist[i]+list(server_info[0])
    for i in range(len(serverlist)):
        del serverlist[i][2]
    return serverlist
def KfServers():
    KF_SQL='select game_server,nation,g_id,self_city,layer_id from kfgz_nation_result where season_id=((select max(season_id) from kfgz_season_info)-0)  order by layer_id,g_id,self_city desc ,opp_city;'
    kf_server_result=mysql_bsconnect(sql=KF_SQL,host=KfIp,db_name=KfdbName)
    return kf_server_result
def getHefuList():
    HF_SQL='select server_flag,name from server where status&2=2 and mixflag=1 and update_date>\''+options.HF_DATE+'\';'
    server_result=mysql_bsconnect(sql=HF_SQL,host=bsdbHost,db_name=bsDb)
    hf_servers={}
####0
    #print server_result
    for i in server_result:
        S_server=i
        FLAG=True
        server_flag=i[0]
        name=i[1]
        while (FLAG):
            t_server=[]
            #M_HF_SQL="select server_flag,name,status from server where server_flag = '"+server_flag+"' and concat('#', mergedServer, '#') like '%#"+name+"#%';"
            #M_HF_SQL="select server_flag,name,status from server where server_flag = '%s' and concat('#', mergedServer, '#') like '%%#%s#%%' limit 1;"%(server_flag,name)
            M_HF_SQL="select server_flag,name,status from server where server_flag = '%s' and concat('#', mergedServer, '#') like '%%#%s#%%' order by status desc;"%(server_flag,name)
            t_server=mysql_bsconnect(sql=M_HF_SQL,host=bsdbHost,db_name=bsDb)
###1
            #print t_server
            #print hf_servers
            if not len(t_server):
                print server_flag+name
                FLAG=False
                continue
            if t_server[0][2]==9:
                hf_servers[S_server[0]+'_'+S_server[1]]=t_server[0][0]+'_'+t_server[0][1]
                #print t_server[0][0]+'_'+t_server[0][1]
                FLAG=False
            else:
                server_flag=t_server[0][0]
                name=t_server[0][1]
                #print server_flag+name
    return hf_servers
def DealData(hflist,serverlist,kflist):
    kf_list=[]
    for k in kflist:
        temp=list(k)
        temp.append(temp[4])
        kf_list.append(temp)
#至尊组降级精锐组
    for s in kf_list:
        if len(s)==6 and s[5]==4:
            temp=[]
            s.append(111)
            temp.append(s)
            for j in kf_list:
                if len(j)==6 and j[5]==4:
                    if j[2]==s[2]:
                            j.append(111)
                            temp.append(j)
            temp.sort(key=lambda x:x[3])
            temp[0][4]=3
            temp[1][4]=3
#精锐组降级
    for s in kf_list:
        if len(s)==6 and s[5]==3:
            temp=[]
            s.append(111)
            temp.append(s)
            for j in kf_list:
                if len(j)==6 and j[5]==3:
                    if j[2]==s[2]:
                            j.append(111)
                            temp.append(j)
            temp.sort(key=lambda x:x[3])
            if temp[0][3]!=temp[1][3]:
                temp[0][4]=2
#平民组升级
    for s in kf_list:
        if len(s)==6 and s[5]==2:
            temp=[]
            s.append(111)
            temp.append(s)
            for j in kf_list:
                if len(j)==6 and j[5]==2:
                    if j[2]==s[2]:
                            j.append(111)
                            temp.append(j)
            temp.sort(key=lambda x:x[3],reverse=True)
            if temp[0][3]!=temp[1][3]:
                temp[0][4]=3
            else:
                temp[0][4]=3
                temp[1][4]=3
#精锐组升级
    temp=[]
    for s in kf_list:
        if  len(s)==7 and s[5]==3:
            temp.append(s)
    temp.sort(key=lambda x:x[3],reverse=True)
    for i in range(int(KingNum)*2+addNum):
        temp[i][4]=4
#####合服处理   
    for i in kf_list:
        if i[0] in hflist:
            server_name=hflist[i[0]]
            if i[4]==3:
                force_id=i[1]
                group_id=i[2]
                city=i[3]
                old_rank=i[5]
                for server in kf_list:
                    if server[0]==server_name and server[1]==force_id and server[4]==2:
                        server[4]=3
                        server[2]=group_id
                        server[3]=city
                        server[5]=old_rank
            elif i[4]==4:
                force_id=i[1]
                group_id=i[2]
                city=i[3]
                old_rank=i[5]
                for server in kf_list:
                    if server[0]==server_name and server[1]==force_id:
                        server[4]=4
                        server[2]=group_id
                        server[3]=city
                        server[5]=old_rank
#删除在跨服list中的合服servers
    for server in kf_list:
        if server[0] in hflist:
            kf_list.remove(server)
    for s in serverlist:
        for i in kf_list:
            if s[0]==i[0] and s[3]==i[1]:
                s+=i[2:]
                break
            else:
                continue
        if len(s)<10:
            temp=[0,0,0,0,000]
            s+=temp
        if s[4]<5:
            s[7]=1
        elif s[7]==1 or s[7]==0:
            s[7]=2
    #print len(serverlist)
    count=0
    for i in serverlist:
        if i[7]==4:
            count=count+1
    if int(KingNum)*6 >count:
        print '至尊组不够，还需要：%d' % (int(KingNum)*6-count)
        sys.exit(1)
    else:
        delnum=count-int(KingNum)*6
        #print delnum
        print '需要删除%d个至尊组---%d' % (delnum,count)
    zhizunlist=[]
    for i in serverlist:
        if i[7]==4 and i[8]==3:
            zhizunlist.append(i)
    #print zhizunlist
    zhizunlist.sort(key=lambda x:x[6],reverse=True)
    #print zhizunlist
    for i in range(len(zhizunlist)):
        if i >= len(zhizunlist)-delnum:
            zhizunlist[i][7]=3
    #print zhizunlist
    zhizunlistt=[]
    for i in serverlist:
        if i[7]==4:
            zhizunlistt.append(i)
    #print zhizunlistt
    #print len(zhizunlistt)
    #print len(serverlist)
    #sys.exit(1)
    data = '游戏服,开服时间,'+options.lv+'级周活跃人数,所属国家,国家等级,上一届国战分组ID,上一届占城数,这一届排赛分组结果,上一届排赛结果\n'
    for i in serverlist:
        if i != len(serverlist)-1:
            i=i[0:10]
            data1='%s,%s,%s,%s,%s,%s,%s,%s,%s' % (i[0],i[1],int(i[2]),int(i[3]),int(i[4]),int(i[5]),int(i[6]),int(i[7]),int(i[8]))
            data1 += '\n'
            data += data1
        else:
            i=i[0:10]
            data1='%s,%s,%s,%s,%s,%s,%s,%s,%s' % (i[0],i[1],int(i[2]),int(i[3]),int(i[4]),int(i[5]),int(i[6]),int(i[7]),int(i[8]))
            data += data1
    fileName=options.game+'_'+options.language+'_kfgz_'+time.strftime('%Y%m%d%H',time.localtime(time.time()))+'.csv'
    f = open(fileName,'w')
    for l in data.split('\n'):
        if l[:-1].strip():
            #print l
            f.write(l+'\n')
    f.close()
    bodyName=options.game+'_'+options.language+'_kfgz_'+time.strftime('%Y%m%d%H',time.localtime(time.time()))+'.txt'
    f = open(bodyName,'w')
    f.write('Dear 运营：\n&nbsp;&nbsp;&nbsp;&nbsp;跨服国战排赛结果见附件！\n请运营根据结果自己检查下，可能需要对各组排赛进行细调！')
    f.close()
    cmd = 'iconv -f UTF8 -t GB18030 %s -o %s.bak && mv %s.bak %s' %(fileName,fileName,fileName,fileName)
    print cmd
    os.system(cmd)
    sendEmail(fileName,bodyName)
if __name__ == '__main__':
    if len(sys.argv)<4 and sys.argv[1] != '-h' and sys.argv[1] != '--help':
        print '''Usage:  python %s -g gcld -L cn -l80 -n7 -d"2014-07-20 00:00:00" -H"2014-07-15 00:00:00"
        python %s -h|--help
        ''' % (sys.argv[0],sys.argv[0])
        sys.exit(1)
    options = getopts()
    init()
    #bodyName='gchw_vn_kfgz_2015010916.txt'
    #fileName='gchw_vn_kfgz_2015010916.csv'
    #sendEmail(fileName,bodyName)
    #print KfIp + bsDb + pwd + preDb + KfdbName + KingNum + str(addNum) + IncludeYxs  + ExcludeYxs + options.KF_DATE + options.HF_DATE 
    serverlist=getAliveOpenServers()
    #print serverlist
    kflist=KfServers()
    #print kflist
    hflist=getHefuList()
    #print hflist
    #print len(hflist)
    DealData(hflist,serverlist,kflist)
