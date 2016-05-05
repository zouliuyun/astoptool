#!/usr/bin/env python
#-*- coding:utf8 -*-
import os, sys, re, json, datetime
import common
from fabric.api import *
from arg import *

def versionCheckPlatform(platform):
    file_exists = run('test -f {}/{}/version.lua'.format(remoteTempDir, platform), warn_only=True).succeeded
    if not file_exists:
        raise Exception('无法在本次上传的资源文件中找到{0}/version.lua, 请确认updateType中的{0}是否填写正确。'.format(platform))
    onlineTestVersionLuaVersion = run("grep 'sys_version.game' %s/%s/version.lua"%(remoteTempDir, platform)).split('"')[1]
    if onlineTestVersionLuaVersion != version :
        raise Exception("测试环境中的version为:%s, 需要更新的版本为:%s, 不匹配，请确认"%(onlineTestVersionLuaVersion, version))

def sys_version_client_lock_check(platform):
    online_sys_version_client = run("grep 'sys_version.client' %s/%s/version.lua"%(wwwDir, platform)).split('"')[1] 
    upcoming_sys_version_client = run("grep 'sys_version.client' %s/%s/version.lua"%(remoteTempDir, platform)).split('"')[1] 
    if online_sys_version_client != upcoming_sys_version_client:
        raise Exception("本次上传的zip文件中sys_version.client为: {}, 测试环境中在使用的sys_version.client为: {}, 不一致。".format(upcoming_sys_version_client, online_sys_version_client))

def versionCheck():
    for each_type in updateTypes:
        versionCheckPlatform(each_type)
        if sys_version_client_lock:
            sys_version_client_lock_check(each_type)

def update_type_pattern_check(updateTypes):
    pattern = r'^\w+(,\w+){0,}$'
    if not re.match(pattern, updateTypes):
        raise Exception('您所填入的updateType不在允许的范围内，请重新填写。正确示例:appstore,jailbreak')

def backupRes():
    backupDir = "/app/opbak/mobileWwwTestUpdateBackup/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    run("mkdir -p " + backupDir)
    run("if [ -e %s/%s ];then cp -r %s/%s %s/;fi"%(wwwDir, version, wwwDir, version, backupDir))

    for each_type in updateTypes:
        run("cp -r %s/%s %s/"%(wwwDir, each_type, backupDir))

def scriptCheck(filename):
    curDir = os.path.abspath(os.path.dirname(__file__))
    getUpdateDirShell = remoteShellDir + "/" + filename
    remoteMd5 = run("if [ -f %s ];then md5sum %s|awk '{print $1}';fi"%(getUpdateDirShell, getUpdateDirShell))
    localMd5 = common.calMd5(curDir + "/" + filename)
    if remoteMd5 != localMd5:
        put(curDir + "/" + filename, "%s/"%remoteShellDir)

def calZipFile():
    scriptCheck("get_update_dir.py")
    scriptCheck("make_www_diff_file.py")
    scriptCheck("mobile_www_cdn_upload.py")
    #获取在线资源目录中，需要将差异文件放入其中的目录
    set_type = 'appstore' #其实已经不再需要这个参数，为了减少改动，保持兼容性，指定一下
    run("python %s/make_www_diff_file.py '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s'"%(remoteShellDir, version, startZipVersion, game, hd, cdn, wwwDir, set_type, language))

@task
def start():
    run("mkdir -p %s "%remoteShellDir)
    global remoteTempDir
    remoteTempDir = "/app/opbak/mobileWwwTestUpdate/%s/%s/%s" %(game, language, version)
    with lcd("/app/online/%s/frontend/%s/%s"%(game, language, version)):
        local("dos2unix md5.txt")
        local("chown virtual_user.virtual_user md5.txt")
        local("md5sum -c md5.txt")
        run("rm -rf %s && mkdir -p %s"%(remoteTempDir, remoteTempDir))
        with cd(remoteTempDir):
            zipExsits = run("if [ -f %s.zip ];then echo 1;else echo 0;fi"%version)
            if zipExsits == "1":
                localZipMd5 = common.calMd5("/app/online/%s/frontend/%s/%s/%s.zip"%(game, language, version, version))
                remoteZipMd5 = run("md5sum %s.zip|cut -d ' ' -f1"%version)
                if localZipMd5.strip() != remoteZipMd5.strip():
                    print "开始上传zip包 ..."
                    put(version + ".zip", remoteTempDir)
            else:
                put(version + ".zip", remoteTempDir)
            put("md5.txt", remoteTempDir)
            run("dos2unix md5.txt")
            run("md5sum -c md5.txt")
            run("unzip -o -q %s.zip"%version )
    versionCheck()
    backupRes()
    with cd(remoteTempDir):
        run("cp -r %s %s/"%(version, wwwDir))
    if zipDiff:
        calZipFile()
    with cd(remoteTempDir):
        for each_type in updateTypes:
            run("cp -rf {0} {1}/".format(each_type, wwwDir))

    local("rm -rf /app/online/%s/frontend/%s/%s"%(game,language,version))


@task
def update():
    env.user = "astd"
    env.key_filename = ["/home/astd/.ssh/id_rsa"]
    env.port = port
    if gateway:
        env.gateway = gateway
    execute(start, hosts=[ip])
    print('Done!')

def init(Game, Language, Version, UpdateType, Hd):
    global version, updateTypes, language, game, hd, wwwDir, zipDiff, gateway
    version = Version
    update_type_pattern_check(UpdateType)
    updateTypes = UpdateType.strip().split(',')
    language = Language
    game = Game
    hd = Hd
    global remoteShellDir
    remoteShellDir = "/app/opbin/workspace"
    if not version or not updateTypes or not language or not game:
        raise Exception("参数不完整")
    if not re.match(r'[0-9]+(\.[0-9]+){3}', version):
        raise Exception("版本号:%s 不符合规则"%version)


    global ip, startZipVersion, cdn, port, sys_version_client_lock
    wwwDir = gameOption("mobile_www_root_test")
    ip = gameOption("mobile_www_ip")
    port = gameOption("mobile_www_port", type="int", default=22)
    startZipVersion = gameOption("mobile_www_start_zip_version")
    cdn = gameOption("mobile_www_cdn", default='false')
    zipDiff = gameOption("mobile_www_diff", type="bool", default=True)
    gateway = gameOption("gateway", default="")
    sys_version_client_lock = gameOption("sys_version_client_lock", type="bool", default=False)
    update()
