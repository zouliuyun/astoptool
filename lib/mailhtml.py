#!/usr/bin/env python
#-*- coding:utf8 -*-

import datetime,os,re

class mailhtml:
    def __init__(self,filename,head):
        '''
            filename:文件名称
            head:html表格头
        '''
        now = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        curdir = os.path.dirname(os.path.abspath(__file__))
        templateFilePath = curdir + "/../template/mailhtml.html"
        filePath = "%s/../file/%s_%s.html"%(curdir,filename,now)
        f = open(filePath,"w")
        f.close()
        fileObj = open(filePath,"a+")
        tempObj = open(templateFilePath,"r")
        i = tempObj.readline()
        while i:
            if not re.search(r'xxxxxxxxxxxxxxxxx',i):
                fileObj.write(i)
            else:
                break
            i = tempObj.readline()
        fileObj.write("\t<tr><td colspan=2 class=head style='background:black;color:white;font-size:20px;text-align:center;'>%s</td></tr>\n"%head)
        self.fileObj = fileObj
        self.tempObj = tempObj
    def add(self,*args,**kwargs):
        self.fileObj.write("\t<tr>")
        for i in range(len(args)):
            if i == 0:
                self.fileObj.write("<th width=200>%s</th>"%args[i])
            else:
                color = kwargs.get("color","black")
                self.fileObj.write("<td class='%s mytd'><pre>%s</pre></td>"%(color,str(args[i])))
        self.fileObj.write("</tr>\n")
    def getCon(self):
        tempSeek = self.tempObj.tell()
        self.fileObj.seek(0)
        str = self.fileObj.read() + self.tempObj.read()
        #str = self.fileObj.read() 
        self.tempObj.seek(tempSeek)
        return str
    def __del__(self):
        line = self.tempObj.readline()
        while line:
            self.fileObj.write(line)
            line = self.tempObj.readline()
        self.fileObj.close()
        self.tempObj.close()
if __name__ == "__main__":
    m = mailhtml("cc","测试而已")
    m.add("表格1","内容1",color="red")
    m.add("表格2","内容2",color="black")
    m.add("表格3","内容3",color="red")
    import sendmail
    #sendmail_zouly.sendmail(m.getCon(),"zouly@game-reign.com","测试邮件",files=['/app/opbin/work/bible/lib/sendmail.py'])
    sendmail_zouly.sendmail(m.getCon(),"zouly@game-reign.com","测试邮件")
