#!/usr/bin/env python
#-*- coding:utf8 -*-

from arg import *
from fabric.api import execute,run,env
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
    for each_type in updateTypes:
        versionCheckPlatform(each_type)

def update_type_pattern_check(updateTypes):
    pattern = r'^\w+(,\w+){0,}$'
    if not re.match(pattern, updateTypes):
        raise Exception('您所填入的updateType不在允许的范围内，请重新填写。正确示例:appstore,jailbreak')

def backupRes():
    backupDir = "/app/opbak/mobile_www_backup/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    cmd("mkdir -p " + backupDir)
    cmd("if [ -e %s/%s ];then cp -r %s/%s %s/;fi"%(onlineDir,version,onlineDir,version,backupDir))
    for each_type in updateTypes:
        cmd("cp -r %s/%s %s/"%(onlineDir, each_type, backupDir))

def fabriccmd(cmdstr):
    try:
        from fabric.api import output as output_fabric
        env.user = 'root'
        output_fabric.stdout = False
        return run(cmdstr, timeout=120)
    except Exception, e:
        print('命令执行超时:{}'.format(e))
        return None

def resRsyncResult():
    try:
        print "等待30秒钟同步资源目录..."
        sys.stdout.flush()
        time.sleep(30)
        rsync_module = gameOption("rsync_module",default="").strip()
        rsync_root = gameOption("rsync_root",default="").strip()
        rsync_backup_ip = gameOption("rsync_backup_ip",default="").strip()
        rootSshObj = ssh.ssh(ip,port=port,user="root")
        if rsync_module != "" and rsync_root != "" and rsync_backup_ip != "" :
            for i in range(6):
                out = execute(fabriccmd,'''cd %s && rsync -art -R --dry-run --delete --out-format="%%n" ./ %s::%s --password-file=/etc/rsyncd.secret'''%(rsync_root,rsync_backup_ip,rsync_module), hosts=[ip])[ip]
                if out == None:
                    break 
                elif out.strip() != "":
                    print "资源暂未完全同步到备用下载点,等待60s后重新检查..."
                    sys.stdout.flush()
                    time.sleep(60)
                else:
                    print "资源同步完毕！"
                    break
            else:
                print "WARNNING: 资源有未同步的情况，30s之后将会更新version.lua，或者手动终止任务!!!!!!!"
                sys.stdout.flush()
                time.sleep(30)
    except Exception,e10:
        print "WARNNING:检查资源同步进度失败!err:%s"%str(e10)

def resCopyToOnline():    
    #获取在线资源目录中，需要将差异文件放入其中的目录
    localDir = os.path.abspath(os.path.dirname(__file__))
    scriptMd5 = cmd("if [ -f /app/opbin/workspace/get_update_dir.py ];then md5sum /app/opbin/workspace/get_update_dir.py |awk '{print $1}';fi")
    localScriptMd5 = common.calMd5(localDir + "/get_update_dir.py")
    if scriptMd5 != localScriptMd5:
        sshobj.put(localDir + "/get_update_dir.py",remote_path="/app/opbin/workspace/")
    #将测试环境中最新的版本资源目录复制到线上环境
    if keepBinaryFile:
        cmd("cp -r %s/%s %s/"%(onlineTestDir,version,onlineDir))
    #复制最新版本到各版本的差异包到线上
    if zipMode:
        set_update_type = 'appstore' #已无实际意义，加上只是为了保持兼容性
        oldDirs = json.loads(cmd("python /app/opbin/workspace/get_update_dir.py '%s' '%s' '%s' '%s' '%s'"%(onlineDir,startVersion,version,set_update_type,hd)))
        if not oldDirs["result"]:
            raise Exception(oldDirs["msg"])
        oldDirsList = oldDirs["dir"]
        for res_type in ["res","res_30lv"]:
            for dir in oldDirsList:
                if dir == version and res_type == "res":
                    print "%s 版本跟需要更新的版本一致，不需要差异包"%dir
                    sys.stdout.flush()
                    continue
                if res_type == "res":
                    zipname = version.strip()
                elif res_type == "res_30lv":
                    zipname = version.strip() + "_30lv"
                else:
                    print "res_type:%s not sruport!"%res_type
                    sys.exit(1)
                print "开始处理%s的差异包%s..."%(dir,zipname)
                sys.stdout.flush()
                if hd:
                    for t in ["res","hd_res","res_64","hd_res_64"]:
                        dirCheck = cmd("if [ -d %s/%s/%s ];then echo 1;else echo 0;fi"%(onlineDir,dir,t))
                        if dirCheck.strip() == "1":
                            if res_type == "res":
                                cmd("cp %s/%s/%s/%s.zip %s/%s/%s/"%(onlineTestDir,dir,t,zipname,onlineDir,dir,t))
                                cmd("cp %s/%s/%s/%s.lua %s/%s/%s/"%(onlineTestDir,dir,t,zipname,onlineDir,dir,t))
                                cmd("if [ -f %s/%s/%s/index.lua ];then cp %s/%s/%s/index.lua %s/%s/%s/;fi"%(onlineTestDir,dir,t,onlineTestDir,dir,t,onlineDir,dir,t))
                                #复制不带.zip包名的zip包
                                cmd("if [ -f %s/%s/%s/%s ];then cp %s/%s/%s/%s %s/%s/%s/;fi"%(onlineTestDir,dir,t,zipname, onlineTestDir,dir,t,zipname, onlineDir,dir,t))
                            elif res_type.strip() == "res_30lv":
                                res_30lv_check = cmd("if [ -f %s/%s/%s/res_30lv.lua ];then echo 1;else echo 0;fi"%(onlineDir,dir,t))
                                if res_30lv_check.strip() == "1":
                                    cmd("cp %s/%s/%s/%s.zip %s/%s/%s/"%(onlineTestDir,dir,t,zipname,onlineDir,dir,t))
                                    cmd("cp %s/%s/%s/%s.lua %s/%s/%s/"%(onlineTestDir,dir,t,zipname,onlineDir,dir,t))
                                    #复制不带.zip包名的zip包
                                    cmd("if [ -f %s/%s/%s/%s ];then cp %s/%s/%s/%s %s/%s/%s/;fi"%(onlineTestDir,dir,t,zipname, onlineTestDir,dir,t,zipname, onlineDir,dir,t))
                        else:
                            print "%s/%s/%s 不存在"%(onlineDir,dir,t)
                            sys.stdout.flush()
                else:
                    if res_type == "res":
                        cmd("cp -r %s/%s/%s.zip %s/%s/"%(onlineTestDir,dir,zipname,onlineDir,dir))
                        cmd("cp -r %s/%s/%s.lua %s/%s/"%(onlineTestDir,dir,zipname,onlineDir,dir))
                        cmd("if [ -f %s/%s/index.lua ];then cp %s/%s/index.lua %s/%s/;fi"%(onlineTestDir,dir,onlineTestDir,dir,onlineDir,dir))
                        #复制不带.zip包名的zip包
                        cmd("if [ -f %s/%s/%s ];then cp %s/%s/%s %s/%s/;fi"%(onlineTestDir,dir,zipname, onlineTestDir,dir,zipname, onlineDir,dir))
                    elif res_type == "res_30lv":
                        res_30lv_check = cmd("if [ -f %s/%s/res_30lv.lua ];then echo 1;else echo 0;fi"%(onlineDir,dir))
                        if res_30lv_check.strip() == "1":
                            cmd("cp -r %s/%s/%s.zip %s/%s/"%(onlineTestDir,dir,zipname,onlineDir,dir))
                            cmd("cp -r %s/%s/%s.lua %s/%s/"%(onlineTestDir,dir,zipname,onlineDir,dir))
                            #复制不带.zip包名的zip包
                            cmd("if [ -f %s/%s/%s ];then cp %s/%s/%s %s/%s/;fi"%(onlineTestDir,dir,zipname, onlineTestDir,dir,zipname, onlineDir,dir))
    #判断是否等待资源同步完毕再更新version.lua
    if waitRsync:
        resRsyncResult()
    print "开始更新version.lua文件..."
    for each_update_type in updateTypes:
        print("cp -rf %s/%s %s/"%(onlineTestDir,each_update_type,onlineDir))
        cmd("cp -rf %s/%s %s/"%(onlineTestDir,each_update_type,onlineDir))
        #手游debug模式开关，线上一定置为0
        cmd("grep 'sys_version.debug' %s/%s/version.lua;if [ $? -eq 0 ];then sed -i '/sys_version.debug/s/1/0/g' %s/%s/version.lua;fi"%(onlineDir,each_update_type,onlineDir,each_update_type))

    cmd("if [ -f %s/version.lua ];then cp %s/jailbreak/version.lua %s/version.lua;fi"%(onlineDir,onlineDir,onlineDir))

def update(Game,Language,Version,UpdateTypes,Hd):
    global version,updateTypes,language,game,hd,port,ip,waitRsync, keepBinaryFile
    version = Version
    updateTypes = UpdateTypes.replace(' ', '').split(',')
    language = Language
    game = Game
    hd = Hd
    
    if not version or not updateTypes or not language or not game:
        parser.error("参数不完整")

    print "开始更新..."
    sys.stdout.flush()
    if not re.match(r'[0-9]+(\.[0-9]+){3}',version):
        raise Exception("版本号:%s 不符合规则"%version)
    ip = gameOption("mobile_www_ip")
    port = gameOption("mobile_www_port",type="int",default=22)

    global sshobj
    sshobj = ssh.ssh(ip,port)

    global onlineDir,onlineTestDir,startVersion,zipMode
    onlineDir = gameOption("mobile_www_root")
    onlineTestDir = gameOption("mobile_www_root_test")
    startVersion = gameOption("mobile_www_start_zip_version")
    zipMode = gameOption("mobile_www_diff",type="bool")
    waitRsync = gameOption("mobile_www_wait_rsync",type="bool",default=False)
    keepBinaryFile = gameOption("mobile_www_keep_binary_file", type="bool", default=True)

    cmd("test -d " + onlineDir)
    cmd("test -d " + onlineTestDir)
    cmd("test -d " + onlineTestDir + "/" + version)

    versionCheck()
    backupRes()
    resCopyToOnline()

    print('Done!')

if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("-v","--version",dest="version",help="更新版本，比如:1.1.1.1")
    parser.add_option("-t","--updateType",dest="updateType",help="更新类型，比如:appstore")
    parser.add_option("-l","--language",dest="language",help="更新语种")
    parser.add_option("-g","--game",dest="game",help="更新语种")
    parser.add_option("-H",dest="hd",action="store_true",help="是否高清模式")

    (options, args) = parser.parse_args()
    version = options.version
    update_type_pattern_check(options.UpdateType)
    updateTypes = options.UpdateType.strip()
    language = options.language
    game = options.game
    hd = options.hd
    update(game,language,version,updateTypes,hd)
