#!/usr/bin/env python
#-*- coding:utf8 -*-

from ftplib import FTP
import os,sys,hashlib
from StringIO import StringIO
from optparse import OptionParser
import optparse


def CalcMD5(filepath):
    with open(filepath,'rb') as f:
        md5obj = hashlib.md5()
        md5obj.update(f.read())
        hash = md5obj.hexdigest()
        return hash

def file_exists_check(filename) :
    if not os.path.exists(filename):
       return False
    else:
       return True
def createdir(dir):
    list = ftp.nlst()
    if dir not in list:
        ftp.mkd(dir)

#自定义上传内容
def cust_upload(localpath,remotepath):
    for dir in remotepath.split("/"):
        if dir.strip() == "":
            continue
        createdir(dir)
        ftp.cwd(dir)
    filename = os.path.basename(localpath)
    dirname = os.path.dirname(localpath)
    os.chdir(dirname)
    print "开始上传%s..."%filename
    upload_file(filename)
    print "上传完毕!"

def upload_file(f1) :
    ftp.storbinary("STOR %s"%f1,open(f1))

def ls_dir(dir):
    ftp.cwd(dir)
    for i in ftp.nlst():
        print i
def arg_check(str):
    if str == None or str.strip() == "":
        parser.print_help()
        sys.exit(1)
def connFtp(host,port,user,password):
    global ftp,list_file
    ftp = FTP()
    ftp.connect(host=host,port=port)
    ftp.login(user,password)
    ftp.getwelcome()
    ftp.cwd(remote_path)
    list_file=ftp.nlst()
if __name__ == "__main__" :
    global parser
    usage = "usage: %prog [options] arg"  
    parser = OptionParser(usage)
    parser.add_option("-t", "--type", dest="type",action="choice",choices=["ls","ftp"], help="upload type:{ls|ftp}")  
    parser.add_option("-d", "--dir", dest="dir", help="ls dir, eg:3.5.0.66")  
    parser.add_option("-h", "--host", dest="host", help="cdn ftp hostt")  
    parser.add_option("-p", "--port", dest="port", help="cdn ftp port")  
    parser.add_option("-u", "--user", dest="user", help="cdn ftp user")  
    parser.add_option("-P", "--password", dest="password", help="cdn ftp password")  
    parser.add_option("-R", "--rootdir", dest="rootdir", help="cdn ftp rootdir")  
    parser.add_option("-r", "--remotedir", dest="remotedir", help="cdn dir path,not need cdn06.aoshitang.com")  
    parser.add_option("-l", "--localfile", dest="localfile", help="local file path")  
    group1 = optparse.OptionGroup(parser, "cdn dir list",
                        "-t ls -h host -p port -P pwd -R rootdir -d listDir")
    parser.add_option_group(group1)
    group1 = optparse.OptionGroup(parser, "custom file upload",
                        "-t ftp -h host -p port -P pwd -R rootdir -r cdnDir(not need cdn06.aoshitang.com this dir) -l localFilePath")
    parser.add_option_group(group1)
    (options, args) = parser.parse_args() 
    
    dir = options.dir
    remotedir = options.remotedir
    localfile = options.localfile
    arg_check(type)

    global remote_path
    remote_path = options.rootdir
    connFtp(options.host,options.port,options.user,options.password)
    #资源包版本
    if type == "ls":
        arg_check(dir)
        ls_dir(dir)
    elif type == "ftp":
        arg_check(remotedir)
        arg_check(localfile)
        cust_upload(localfile,remotedir)
    else:
        print "not surport action %s"%type
        sys.exit(1)
