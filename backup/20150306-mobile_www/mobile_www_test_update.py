#!/usr/bin/env python
#-*- coding:utf8 -*-
import os,sys,re,json,datetime
import common
from fabric.api import *
from arg import *

def versionCheckPlatform(platform):
    onlineTestVersionLuaVersion = run("grep 'sys_version.game' %s/%s/version.lua"%(remoteTempDir,platform)).split('"')[1]
    if onlineTestVersionLuaVersion != version :
        raise Exception("测试环境中的version为:%s,需要更新的版本为:%s,不匹配，请确认"%(onlineTestVersionLuaVersion,version))
def versionCheck():
    if updateType in ["appstore","all"]:
        versionCheckPlatform("appstore")
    if updateType in ["jailbreak","all"]:
        versionCheckPlatform("jailbreak")
    if updateType in ["appstore64"]:
        versionCheckPlatform("appstore64")
def backupRes():
    backupDir = "/app/opbak/mobileWwwTestUpdateBackup/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    run("mkdir -p " + backupDir)
    run("if [ -e %s/%s ];then cp -r %s/%s %s/;fi"%(wwwDir,version,wwwDir,version,backupDir))
    if updateType in ["appstore","all"]:
        run("cp %s/appstore/version.lua %s/appstore-version.lua"%(wwwDir,backupDir))
    if updateType in ["jailbreak","all"]:
        run("cp %s/jailbreak/version.lua %s/jailbreak-version.lua"%(wwwDir,backupDir))
    if updateType in ["appstore64"]:
        run("cp %s/appstore64/version.lua %s/appstore64-version.lua"%(wwwDir,backupDir))
def scriptCheck(filename):
    curDir = os.path.abspath(os.path.dirname(__file__))
    getUpdateDirShell = remoteShellDir + "/" + filename
    remoteMd5 = run("if [ -f %s ];then md5sum %s|awk '{print $1}';fi"%(getUpdateDirShell,getUpdateDirShell))
    localMd5 = common.calMd5(curDir + "/" + filename)
    if remoteMd5 != localMd5:
        put(curDir + "/" + filename,"%s/"%remoteShellDir)

def calZipFile():
    scriptCheck("get_update_dir.py")
    scriptCheck("make_www_diff_file.py")
    scriptCheck("mobile_www_cdn_upload.py")
    #获取在线资源目录中，需要将差异文件放入其中的目录
    run("python %s/make_www_diff_file.py '%s' '%s' '%s' '%s' '%s' '%s' '%s'"%(remoteShellDir,version,startZipVersion,game,hd,cdn,wwwDir,updateType))
@task
def start():
    run("mkdir -p %s "%remoteShellDir)
    global remoteTempDir
    remoteTempDir = "/app/opbak/mobileWwwTestUpdate/%s/%s" %(game, version)
    with lcd("/app/online/%s/frontend/%s/%s"%(game,language,version)):
        local("dos2unix md5.txt")
        local("chown virtual_user.virtual_user md5.txt")
        local("md5sum -c md5.txt")
        run("rm -rf %s && mkdir -p %s"%(remoteTempDir,remoteTempDir))
        with cd(remoteTempDir):
            zipExsits = run("if [ -f %s.zip ];then echo 1;else echo 0;fi"%version)
            if zipExsits == "1":
                localZipMd5 = common.calMd5("/app/online/%s/frontend/%s/%s/%s.zip"%(game,language,version,version))
                remoteZipMd5 = run("md5sum %s.zip|cut -d ' ' -f1"%version)
                if localZipMd5.strip() != remoteZipMd5.strip():
                    put(version + ".zip",remoteTempDir)
            else:
                put(version + ".zip",remoteTempDir)
            #put(version + ".zip",remoteTempDir)
            put("md5.txt",remoteTempDir)
            run("dos2unix md5.txt")
            run("md5sum -c md5.txt")
            run("unzip -o -q %s.zip"%version )
            #appstore64 必须包含main.lua，否则为appstore32或者越狱
            if updateType in ["appstore64"]:
                run("test -f %s/main.lua"%version)
            #if hd:
            #    res_64_dir = run("if [ -d %s/res_64 ];then echo 1 ;else echo 0 ;fi"%version)
            #    hd_res_64_dir = run("if [ -d %s/hd_res_64 ];then echo 1 ;else echo 0;fi"%version)
            #    if res_64_dir.strip() != "1" and hd_res_64_dir.strip() != "1":
            #        print "%s该目录不存在64的资源目录"%version
            #        sys.exit(1)
    versionCheck()
    backupRes()
    with cd(remoteTempDir):
        run("cp -r %s %s/"%(version,wwwDir))
    if zipDiff:
        calZipFile()
    with cd(remoteTempDir):
        #run("cp -r %s %s/"%(version,wwwDir))
        if updateType in ["appstore64"]:
            run("cp -r appstore64/version.lua %s/appstore64/"%wwwDir)
        if updateType in ["appstore","all"]:
            run("cp -r appstore/version.lua %s/appstore/"%wwwDir)
        if updateType in ["jailbreak","all"]:
            run("cp -r jailbreak/version.lua %s/jailbreak/"%wwwDir)
            run("if [ -f %s/version.lua ];then cp jailbreak/version.lua %s/version.lua;fi"%(wwwDir,wwwDir))
    local("rm -rf /app/online/%s/frontend/%s/%s"%(game,language,version))
@task
@runs_once
def update():
    env.hosts = [ip,]
    env.user = "astd"
    env.key_filename = ["/home/astd/.ssh/id_rsa"]
    env.port = port
    env.warn_only = False
    execute(start)
def init(Game,Language,Version,UpdateType,Hd):
    global version,updateType,language,game,hd,wwwDir,zipDiff
    version = Version
    updateType = UpdateType
    language = Language
    game = Game
    hd = Hd
    global remoteShellDir
    remoteShellDir = "/app/opbin/workspace"
    if not version or not updateType or not language or not game:
        parser.error("参数不完整")
    if not re.match(r'[0-9]+(\.[0-9]+){3}',version):
        raise Exception("版本号:%s 不符合规则"%version)
    global ip,startZipVersion,cdn,port
    wwwDir = gameOption("mobile_www_root_test")
    ip = gameOption("mobile_www_ip")
    port = gameOption("mobile_www_port",type="int",default=22)
    #if not port or port.strip() == "":
    #    port = 22
    startZipVersion = gameOption("mobile_www_start_zip_version")
    cdn = gameOption("mobile_www_cdn")
    zipDiff = gameOption("mobile_www_diff",type="bool")
    update()
