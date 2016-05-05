#!/usr/bin/env python
#-*- coding:utf8 -*-
import sys,os,re,hashlib,shutil
import get_update_dir

def CalcMD5(filepath):
    with open(filepath,'rb') as f:
        md5obj = hashlib.md5()
        md5obj.update(f.read())
        hash = md5obj.hexdigest()
        return hash

def getNewMd5Dict(newResDir,file):
    #获取新版本的md5，并且比对res中的md5是否一致
    global newmd5
    newmd5 = {}
    newRes = open(newResDir + "/" + file)
    rows = newRes.readlines()
    newRes.close()
    for row in rows:
        if re.search('md5',row):
            s = row.split('"')
            key = s[1]
            md5 = s[3]
            if key in newmd5:
                print "%s key multipule!"%key
                sys.exit(1)
            newmd5[key] = md5
            if not os.path.exists("%s/%s"%(newResDir,key)):
                print "newfile %s not exists!"%key
                sys.exit(1)
            calmd5 = CalcMD5("%s/%s"%(newResDir,key))
            if calmd5 != md5:
                print "%s md5 not wright!res md5 is:%s , cal md5 is %s"%(key,md5,calmd5)
                sys.exit(1)
def cdnUpload(localfile,cdnPath):
    status = os.system("/app/opbin/workspace/mobile_www_cdn_upload.py  -t ftp  -f '%s.zip' -v '%s'"%(destVersion,oldVersion))
    if status != 0:
        print "cdn upload failed!file is %s/%s.zip"%(oldVersion,destVersion)
        sys.exit(1)
def makeDiff(newResDir,oldResDir,newVersion,oldVersion,cdn):

    oldmd5 = {}
    oldRes = open("%s/res.lua"%oldResDir)
    rows = oldRes.readlines()
    oldRes.close()
    for row in rows:
        if re.search('md5',row):
            s = row.split('"')
            key = s[1]
            md5 = s[3]
            oldmd5[key] = md5

    for newfile in newmd5:
        #新文件在老包不存在需要打包,新文件跟老文件md5指不一致需要打包
        if newfile not in oldmd5.keys():
            shutil.copy("%s/%s"%(newResDir,newfile),newfile)
        elif newmd5[newfile] != oldmd5[newfile]:
            shutil.copy("%s/%s"%(newResDir,newfile),newfile)
    status = os.system("zip -q %s.zip *"%newVersion)
    if status != 0:
        print "zip failed!zip -q %s.zip *"%newVersion
        sys.exit(1)
    
    #zip文件的md5和大小计算
    file_md5 = CalcMD5("%s.zip"%newVersion)
    file_len = os.path.getsize("%s.zip"%newVersion)
    #zip包的md5信息文件
    newmd5file = open("%s.lua"%newVersion,"w")
    newmd5file.write("local updateZipSize = {}\n")
    newmd5file.write('updateZipSize.value = %s;\n'%file_len)
    newmd5file.write('updateZipSize.md5 = "%s"\n'%file_md5)
    newmd5file.write("return updateZipSize;")
    newmd5file.close()
    #攻城手游老版本要使用这个
    indexlua = open("index.lua","w")
    indexlua.write("local updateZipSize = {}\n")
    indexlua.write('updateZipSize.value = %s;\n'%file_len)
    indexlua.write('updateZipSize.md5 = "%s"\n'%file_md5)
    indexlua.write("return updateZipSize;")
    indexlua.close()
    os.system("mv %s.lua %s"%(newVersion,oldResDir))
    os.system("mv index.lua %s"%oldResDir)
    os.system("mv %s.zip %s"%(newVersion,oldResDir))
    if cdn == "true":
        print "开始上传cdn..."
        cdnUpload("%s/%s.zip"%(oldResDir,newVersion),oldVersion)
        cdnUpload("%s/%s.lua"%(oldResDir,newVersion),oldVersion)
        if os.path.exists("%s/index.lua"%oldResDir):
            cdnUpload("%s/index.lua"%oldResDir,oldVersion)
    else:
        print "不需要上传到cdn"
if __name__ == "__main__":
    global dest_dir,work_dir,www_dir
    dest_dir = sys.argv[1]
    #startdir="1.0.0.0"
    startdir = sys.argv[2]
    game = sys.argv[3]
    hd = sys.argv[4]
    cdn = sys.argv[5]
    www_dir = sys.argv[6]
    clientType = sys.argv[7] #用于判断是否为appstore64

    work_dir="/app/opbak/diffdir/" + game

    if dest_dir.strip() == "":
        print "destination dir not exists!"
        sys.exit(1)


    if not os.path.exists(www_dir):
        print "destination dir not exists!"
        sys.exit(1)

    olddirs=get_update_dir.get_dirs(www_dir,startdir,dest_dir,clientType,hd)
    if not olddirs["result"]:
        print olddirs["msg"]
        sys.exit(1)
    os.system("rm -rf %s " %work_dir)
    os.makedirs(work_dir)
    if hd.strip().lower() == "true":
        for type in ["res","hd_res"]:
            if not os.path.isdir("%s/%s/%s"%(www_dir,dest_dir,type)):
                print "%s/%s/%s 不存在,将不进行差异计算"%(www_dir,dest_dir,type)
                continue
            os.chdir(work_dir)
            os.makedirs(type)
            newResDir = "%s/%s/%s"%(www_dir,dest_dir,type)
            getNewMd5Dict(newResDir,"res.lua")
            for olddir in olddirs["dir"]:
                if not os.path.isdir("%s/%s/%s"%(www_dir,olddir,type)):
                    print "%s/%s/%s 不存在,将不进行差异计算"%(www_dir,olddir,type)
                    continue
                print olddir,type
                if olddir == dest_dir:
                    continue
                oldResDir = "%s/%s/%s"%(www_dir,olddir,type)
                if os.path.exists("%s/%s.zip"%(oldResDir,dest_dir)):
                    print "%s/%s.zip 已经存在，将覆盖!"%(oldResDir,dest_dir)
                    #sys.exit(1)
                os.chdir(work_dir)
                os.chdir(type)
                os.makedirs(olddir)
                os.chdir(olddir)
                makeDiff(newResDir,oldResDir,dest_dir,olddir,cdn)
    else:
        os.chdir(work_dir)
        newResDir = "%s/%s"%(www_dir,dest_dir)
        getNewMd5Dict(newResDir,"res.lua")
        for olddir in olddirs["dir"]:
            if olddir == dest_dir:
                continue
            oldResDir = "%s/%s"%(www_dir,olddir)
            if os.path.exists("%s/%s.zip"%(oldResDir,dest_dir)):
                print "%s/%s.zip 已经存在，将覆盖!"%(oldResDir,dest_dir)
                #sys.exit(1)
            os.chdir(work_dir)
            print olddir
            os.makedirs(olddir)
            os.chdir(olddir)
            makeDiff(newResDir,oldResDir,dest_dir,olddir,cdn)
