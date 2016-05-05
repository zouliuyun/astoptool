#!/usr/bin/env python
#-*- coding:utf8 -*-
import sys,os,re,hashlib,shutil

def CalcMD5(filepath):
    with open(filepath,'rb') as f:
        md5obj = hashlib.md5()
        md5obj.update(f.read())
        hash = md5obj.hexdigest()
        return hash

def getNewMd5Dict(www_dir,dest_dir):
    #获取新版本的md5，并且比对res中的md5是否一致
    global newmd5
    newmd5 = {}
    newRes = open("%s/%s/res.lua"%(www_dir,dest_dir))
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
            calmd5 = CalcMD5("%s/%s/%s"%(www_dir,dest_dir,key))
            if calmd5 != md5:
                print "%s md5 not wright!res md5 is:%s , cal md5 is %s"%(key,md5,calmd5)
                sys.exit(1)
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print "Usage: %s src_dir dest_dir www_dir"%sys.argv[0]
        sys.exit(1)
    src_dir = sys.argv[1]
    dest_dir = sys.argv[2]
    www_dir = sys.argv[3]

    work_dir="/app/opbak/tempdiffdir"


    os.system("rm -rf %s && mkdir -p %s" %(work_dir, work_dir))

    if not os.path.exists(www_dir):
        print "www dir %s not exists!"%www_dir
        sys.exit(1)

    getNewMd5Dict(www_dir,dest_dir)
    for olddir in [src_dir]:
        if olddir == dest_dir:
            continue
        if os.path.exists("%s/%s/%s.zip"%(www_dir,olddir,dest_dir)):
            print "%s/%s/%s.zip have exits!"%(www_dir,olddir,dest_dir)
            sys.exit(1)
        os.chdir(work_dir)
        print olddir 
        os.makedirs(olddir)
        os.chdir(olddir)

        oldmd5 = {}
        oldRes = open("%s/%s/res.lua"%(www_dir,olddir))
        rows = oldRes.readlines()
        oldRes.close()
        for row in rows:
            if re.search('md5',row):
                s = row.split('"')
                key = s[1]
                md5 = s[3]
                oldmd5[key] = md5

        for newfile in newmd5:
            if newfile not in oldmd5.keys():
                if not os.path.exists("%s/%s/%s"%(www_dir,dest_dir,newfile)):
                    print "newfile %s not exists!"%newfile
                    sys.exit(1)
                shutil.copy("%s/%s/%s"%(www_dir,dest_dir,newfile),newfile)
            elif newmd5[newfile] != oldmd5[newfile]:
                if not os.path.exists("%s/%s/%s"%(www_dir,dest_dir,newfile)):
                    print "newfile %s not exists!"%newfile
                    sys.exit(1)
                shutil.copy("%s/%s/%s"%(www_dir,dest_dir,newfile),newfile)
        status = os.system("zip -q %s.zip *"%dest_dir)
        if status != 0:
            print "zip failed!zip -q %s.zip *"%dest_dir
            sys.exit(1)
        
        #zip文件的md5和大小计算
        file_md5 = CalcMD5("%s.zip"%dest_dir)
        file_len = os.path.getsize("%s.zip"%dest_dir)
        #老的版本使用的index.lua，为了兼容最早更新用户，所以需要计算
        indexlua = open("index.lua","w")
        indexlua.write("local updateZipSize = {}\n")
        indexlua.write('updateZipSize.value = %s;\n'%file_len)
        indexlua.write('updateZipSize.md5 = "%s"\n'%file_md5)
        indexlua.write("return updateZipSize;")
        indexlua.close()
        if os.path.exists("%s/%s/index.lua"%(www_dir,olddir)):
            os.remove("%s/%s/index.lua"%(www_dir,olddir))
        shutil.move("index.lua","%s/%s"%(www_dir,olddir))
        shutil.move("%s.zip"%dest_dir,"%s/%s"%(www_dir,olddir))
        #zip包的md5信息文件
        newmd5file = open("%s.lua"%dest_dir,"w")
        newmd5file.write("local updateZipSize = {}\n")
        newmd5file.write('updateZipSize.value = %s;\n'%file_len)
        newmd5file.write('updateZipSize.md5 = "%s"\n'%file_md5)
        newmd5file.write("return updateZipSize;")
        newmd5file.close()
        shutil.move("%s.lua"%dest_dir,"%s/%s"%(www_dir,olddir))
        #if language == "cn":
        #    status = os.system("/app/opbin/workspace/cdn_upload.py -t upload -f '%s.zip' -v '%s'"%(dest_dir,olddir))
        #    if status != 0:
        #        print "cdn upload failed!file is %s/%s.zip"%(olddir,dest_dir)
        #        sys.exit(1)
