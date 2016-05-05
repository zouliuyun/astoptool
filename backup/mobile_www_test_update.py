#!/usr/bin/env python
#-*- coding:utf8 -*-
import os,sys,re,json,datetime
import common,config
from fabric.api import *
from lib.arg import *

def versionCheckPlatform(platform):
    onlineTestVersionLuaVersion = run("grep 'sys_version.game' %s/%s/version.lua"%(remoteTempDir,platform)).split('"')[1]
    if onlineTestVersionLuaVersion != version :
        raise Exception("测试环境中的version为:%s,需要更新的版本为:%s,不匹配，请确认"%(onlineTestVersionLuaVersion,version))
def versionCheck():
    if updateType in ["appstore","all"]:
        versionCheckPlatform("appstore")
    if updateType in ["jailbreak","all"]:
        versionCheckPlatform("jailbreak")
def backupRes():
    backupDir = "/app/opbak/mobileWwwTestUpdateBackup/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    run("mkdir -p " + backupDir)
    run("if [ -e %s/%s ];then cp -r %s/%s %s/;fi"%(wwwDir,version,wwwDir,version,backupDir))
    if updateType in ["appstore","all"]:
        run("cp %s/appstore/version.lua %s/appstore-version.lua"%(wwwDir,backupDir))
    if updateType in ["jailbreak","all"]:
        run("cp %s/jailbreak/version.lua %s/jailbreak-version.lua"%(wwwDir,backupDir))
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
    run("python %s/make_www_diff_file.py '%s' '%s' '%s' '%s' '%s' '%s'"%(remoteShellDir,version,startZipVersion,game,hd,cdn,wwwDir))
@task
def start():
    run("mkdir -p %s "%remoteShellDir)
    global remoteTempDir
    remoteTempDir = "/app/opbak/mobileWwwTestUpdate/%s/%s" %(game, version)
    with lcd("/app/online/%s/frontend/%s"%(game,version)):
        #local("dos2unix md5.txt")
        #local("chown virtual_user.virtual_user md5.txt")
        #local("md5sum -c md5.txt")
        run("rm -rf %s && mkdir -p %s"%(remoteTempDir,remoteTempDir))
        with cd(remoteTempDir):
            put(version + ".zip",remoteTempDir)
            put("md5.txt",remoteTempDir)
            run("dos2unix md5.txt")
            run("md5sum -c md5.txt")
            run("unzip -o -q %s.zip"%version )
    versionCheck()
    backupRes()
    with cd(remoteTempDir):
        run("cp -r %s %s/"%(version,wwwDir))
        if updateType in ["appstore","all"]:
            run("cp -r appstore/version.lua %s/appstore/"%wwwDir)
        if updateType in ["jailbreak","all"]:
            run("cp -r jailbreak/version.lua %s/jailbreak/"%wwwDir)
    if zipDiff:
        calZipFile()
@task
@runs_once
def update():
    env.hosts = [ip,]
    env.user = "astd"
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
    gameConfig = config.getConfig(game)
    wwwDir = getOption(gameConfig,language,"mobile_www_root_test")
    ip = getOption(gameConfig,language,"mobile_www_ip")
    port = getOption(gameConfig,language,"mobile_www_port")
    if not port or port.strip() == "":
        port = 22
    startZipVersion = getOption(gameConfig,language,"mobile_www_start_zip_version")
    cdn = getOption(gameConfig,language,"mobile_www_cdn")
    zipDiff = getOption(gameConfig,language,"mobile_www_diff",type="bool")
    update()
