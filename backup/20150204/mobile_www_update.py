#!/usr/bin/env python
#-*- coding:utf8 -*-

from arg import *
import optparse,os,sys,re,json,datetime
import ssh,common

def cmd(command):
    status,stdout,error = sshobj.cmd(command)
    if status != 0 :
        raise Exception("[执行]%s\n%s"%(command,error))
    sys.stdout.flush()
    return stdout
def versionCheckPlatform(platform):
    print "%s/%s/version.lua"%(onlineTestDir,platform)
    sys.stdout.flush()
    onlineTestVersionLuaVersion = cmd("grep 'sys_version.game' %s/%s/version.lua"%(onlineTestDir,platform)).split('"')[1]
    if onlineTestVersionLuaVersion != version :
        raise Exception("测试环境中的version为:%s,需要更新的版本为:%s,不匹配，请确认"%(onlineTestVersionLuaVersion,version))
def versionCheck():
    if updateType in ["appstore64"]:
        versionCheckPlatform("appstore64")
    if updateType in ["appstore","all"]:
        versionCheckPlatform("appstore")
    if updateType in ["jailbreak","all"]:
        versionCheckPlatform("jailbreak")
def backupRes():
    backupDir = "/app/opbak/mobile_www_backup/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    cmd("mkdir -p " + backupDir)
    cmd("if [ -e %s/%s ];then cp -r %s/%s %s/;fi"%(onlineDir,version,onlineDir,version,backupDir))
    if updateType in ["appstore64"]:
        cmd("cp %s/appstore64/version.lua %s/appstore64-version.lua"%(onlineDir,backupDir))
    if updateType in ["appstore","all"]:
        cmd("cp %s/appstore/version.lua %s/appstore-version.lua"%(onlineDir,backupDir))
    if updateType in ["jailbreak","all"]:
        cmd("cp %s/jailbreak/version.lua %s/jailbreak-version.lua"%(onlineDir,backupDir))
def resCopyToOnline():    
    #获取在线资源目录中，需要将差异文件放入其中的目录
    localDir = os.path.abspath(os.path.dirname(__file__))
    scriptMd5 = cmd("if [ -f /app/opbin/workspace/get_update_dir.py ];then md5sum /app/opbin/workspace/get_update_dir.py |awk '{print $1}';fi")
    localScriptMd5 = common.calMd5(localDir + "/get_update_dir.py")
    if scriptMd5 != localScriptMd5:
        sshobj.put(localDir + "/get_update_dir.py",remote_path="/app/opbin/workspace/")
    oldDirs = json.loads(cmd("python /app/opbin/workspace/get_update_dir.py '%s' '%s' '%s' '%s' '%s'"%(onlineDir,startVersion,version,updateType,hd)))
    if not oldDirs["result"]:
        raise Exception(oldDirs["msg"])
    oldDirsList = oldDirs["dir"]
    #如果为appstore64，首先检查目标版本中是否存在main.lua
    if updateType == "appstore64":
        if not hd:
            cmd("test -f  %s/%s/main.lua"%(onlineTestDir,version))
        else:
            cmd("if [ -d %s/%s/res ];then test -f %s/%s/res/main.lua;fi"%(onlineTestDir,version,onlineTestDir,version))
            cmd("if [ -d %s/%s/hd_res ];then test -f %s/%s/hd_res/main.lua;fi"%(onlineTestDir,version,onlineTestDir,version))
    #将测试环境中最新的版本资源目录复制到线上环境
    cmd("cp -r %s/%s %s/"%(onlineTestDir,version,onlineDir))
    #复制最新版本到各版本的差异包到线上
    if zipMode:
        for dir in oldDirsList:
            if dir == version:
                print "%s 版本跟需要更新的版本一致，不需要差异包"%dir
                sys.stdout.flush()
                continue
            print "开始处理%s的差异包..."%dir
            sys.stdout.flush()
            if hd:
                for t in ["res","hd_res"]:
                    dirCheck = cmd("if [ -d %s/%s/%s ];then echo 1;else echo 0;fi"%(onlineDir,dir,t))
                    if dirCheck.strip() == "1":
                        cmd("cp %s/%s/%s/%s.zip %s/%s/%s/"%(onlineTestDir,dir,t,version,onlineDir,dir,t))
                        cmd("cp %s/%s/%s/%s.lua %s/%s/%s/"%(onlineTestDir,dir,t,version,onlineDir,dir,t))
                        cmd("if [ -f %s/%s/%s/index.lua ];then cp %s/%s/%s/index.lua %s/%s/%s/;fi"%(onlineTestDir,dir,t,onlineTestDir,dir,t,onlineDir,dir,t))
                    else:
                        print "%s/%s/%s 不存在"%(onlineDir,dir,t)
                        sys.stdout.flush()
            else:
                cmd("cp -r %s/%s/%s.zip %s/%s/"%(onlineTestDir,dir,version,onlineDir,dir))
                cmd("cp -r %s/%s/%s.lua %s/%s/"%(onlineTestDir,dir,version,onlineDir,dir))
                cmd("if [ -f %s/%s/index.lua ];then cp %s/%s/index.lua %s/%s/;fi"%(onlineTestDir,dir,onlineTestDir,dir,onlineDir,dir))
    #将version.lua文件更新到线上
    if updateType in ["appstore64"]:
        cmd("cp %s/appstore64/version.lua %s/appstore64/"%(onlineTestDir,onlineDir))
        #手游debug模式开关，线上一定置为0
        cmd("grep 'sys_version.debug' %s/appstore64/version.lua;if [ $? -eq 0 ];then sed -i '/sys_version.debug/s/1/0/g' %s/appstore64/version.lua;fi"%(onlineDir,onlineDir))
    if updateType in ["appstore","all"]:
        cmd("cp %s/appstore/version.lua %s/appstore/"%(onlineTestDir,onlineDir))
        #手游debug模式开关，线上一定置为0
        cmd("grep 'sys_version.debug' %s/appstore/version.lua;if [ $? -eq 0 ];then sed -i '/sys_version.debug/s/1/0/g' %s/appstore/version.lua;fi"%(onlineDir,onlineDir))
    if updateType in ["jailbreak","all"]:
        cmd("cp %s/jailbreak/version.lua %s/jailbreak/"%(onlineTestDir,onlineDir))
        cmd("grep 'sys_version.debug' %s/jailbreak/version.lua;if [ $? -eq 0 ];then sed -i '/sys_version.debug/s/1/0/g' %s/jailbreak/version.lua;fi"%(onlineDir,onlineDir))
        cmd("if [ -f %s/version.lua ];then cp %s/jailbreak/version.lua %s/version.lua;fi"%(onlineDir,onlineDir,onlineDir))

def update(Game,Language,Version,UpdateType,Hd):
    global version,updateType,language,game,hd
    version = Version
    updateType = UpdateType
    language = Language
    game = Game
    hd = Hd
    
    if not version or not updateType or not language or not game:
        parser.error("参数不完整")

    print "开始更新..."
    sys.stdout.flush()
    if not re.match(r'[0-9]+(\.[0-9]+){3}',version):
        raise Exception("版本号:%s 不符合规则"%version)
    ip = gameOption("mobile_www_ip")
    port = gameOption("mobile_www_port",type="int",default=22)
    #if not port :
    #    port = 22

    global sshobj
    sshobj = ssh.ssh(ip,port)

    global onlineDir,onlineTestDir,startVersion,zipMode
    onlineDir = gameOption("mobile_www_root")
    onlineTestDir = gameOption("mobile_www_root_test")
    startVersion = gameOption("mobile_www_start_zip_version")
    zipMode = gameOption("mobile_www_diff",type="bool")

    cmd("test -d " + onlineDir)
    cmd("test -d " + onlineTestDir)
    cmd("test -d " + onlineTestDir + "/" + version)
    #cmd("! test -d " + onlineDir + "/" + version)

    versionCheck()
    backupRes()
    resCopyToOnline()

if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("-v","--version",dest="version",help="更新版本，比如:1.1.1.1")
    parser.add_option("-t","--updateType",dest="updateType",type="choice",choices=["appstore","jailbreak","all"],help="更新类型，比如:appstore")
    parser.add_option("-l","--language",dest="language",help="更新语种")
    parser.add_option("-g","--game",dest="game",help="更新语种")
    parser.add_option("-H",dest="hd",action="store_true",help="是否高清模式")

    (options, args) = parser.parse_args()
    version = options.version
    updateType = options.updateType
    language = options.language
    game = options.game
    hd = options.hd
    update(game,language,version,updateType,hd)
