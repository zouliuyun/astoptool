#!/usr/bin/env python
#-*- coding:utf8 -*-
import sys,os,json,commands,re,time,datetime
import optparse
from arg import *
import ssh,state,ccthread,common

def null(Str):
    if Str == None or str(Str).lower().strip() == "none" or str(Str).strip() == "" or str(Str).lower().strip() == "null":
        return True
    else:
        return False
def nullCheck(str,msg):
    if null(str):
        print "ERROR: " + msg
        sys.exit(1)
def cmd(cmdStr):
    status,stdout,stderr = wwwSsh.cmd(cmdStr)
    if status != 0 :
        print "ERROR: [%s] execute failed!\nErr:%s\nOutput:%s"%(cmdStr,stderr,stdout)
        sys.exit(1)
    return stdout
def put(localfile,remote_path=None):
    try:
        wwwSsh.put(localfile,remote_path=remote_path)
    except Exception,e:
        raise Exception("上传%s资源到资源服务器%s失败! err: %s" %(localfile,remote_path,str(e)))
def resourceToWww(localdir,www_root,specialScript,remoteResourceDir):
    remoteDir = "%s/%s/update/%s"%(www_root,state.game,remoteResourceDir)
    result = cmd("if [ -e %s ];echo 1 ;then echo 0;fi"%remoteDir)
    if result.strip() == "1":
        print "ERROR: 资源目录选取失败!"
        sys.exit(1)
    cmd("mkdir -p " + remoteDir)
    for file in os.listdir("/app/online/%s/update/%s/"%(state.game,localdir)):
        put("/app/online/%s/update/%s/%s"%(state.game,localdir,file),remote_path=remoteDir)
    cmd("cd %s && dos2unix md5.txt && md5sum -c md5.txt"%remoteDir)
    if not null(specialScript):
        put(specialScript,remote_path=remoteDir)
    cmd("cd %s && rm -f md5.txt && md5sum * > md5.txt"%remoteDir)
def scriptDeploy(sshObj,ip,server):
    '''
    更新脚本的md5比对，如果跟本地的不一致则重新上传
    判断更新操作目录是否存在，如果存在则不再进行更新
    '''
    localmd5 = common.calMd5(updateScriptPath + "/" + updateScript)
    status,out,err = sshObj.cmd("if [ ! -d %s ];then mkdir -p %s;fi"%(remoteLogDir,remoteLogDir))
    if status != 0:
        state.errorResult[server] = "创建工作目录失败" + err
    else:
        status,remotemd5,stderr = sshObj.cmd("if [ -f %s/%s ];then md5sum %s/%s ;fi"%(remoteShellPath,updateScript,remoteShellPath,updateScript))
        if status != 0:
            state.errorResult[server] = stderr
        else:
            if localmd5.strip() != remotemd5.strip():
                try:
                    sshObj.put(updateScriptPath + "/" + updateScript,remote_path=remoteShellPath)
                except Exception,e:
                    state.errorResult[server] = str(e)
        status,out,err = sshObj.cmd("if [ -d /app/opbin/update/%s/%s ];then echo 1;else echo 0;fi"%(state.options.game,remoteWorkDir))
        if status != 0 or out == 1:
            state.errorResult[server] = "/app/opbin/update/%s/%s目录已经存在"%(state.options.game,remoteWorkDir)
def executeUpdate(sshObj,ip,server,sqlOrNot,sqlFile,backendChangeOrNot,backendName,executeVersionList,restart,www_header,www_ip,www_port,replaceFile,addFile,addContent,specialScriptExecuteFirst,versionTag,specialScriptFileName,remoteResourceDir):
    '''
    执行更新脚本
    '''
    print "开始更新:" + server
    sys.stdout.flush()
    argStr = "nohup python " + remoteShellPath + "/" + updateScript + " -g " + state.options.game + " -s " + server + " -H " + www_header + " -i " + www_ip + " -p " + www_port + " -D " + remoteWorkDir + " -V " + versionTag
    if remoteResourceDir:
        argStr += " -d '"+remoteResourceDir+"'"
    if sqlOrNot:
        argStr += " -q '"+sqlOrNot+"'"
    if sqlFile:
        argStr += " -Q '" + sqlFile + "'"
    if backendChangeOrNot:
        argStr += " -b '" + backendChangeOrNot + "'"
    if backendName:
        argStr += " -B '" + backendName + "'"
    if executeVersionList:
        argStr += " -v '" + executeVersionList + "'"
    if restart:
        argStr += " -R '" + restart + "'"
    if replaceFile:
        argStr += " -r '" + replaceFile + "'"
    if addFile:
        argStr += " -a '" + addFile + "'"
    if addContent:
        argStr += " -c '" + addContent + "'"
    if specialScriptFileName:
        argStr += " -o '" + specialScriptFileName + "'"
    if specialScriptExecuteFirst:
        argStr += " -O '" + specialScriptExecuteFirst + "'"
    argStr += " > %s/update_%s.log 2>&1 &"%(remoteLogDir,server)
    #print argStr
    status,out,err = sshObj.cmd(argStr)
    if status !=0 :
        state.errorResult[server] = err
def checkUpdateResult(sshObj,ip,server,restart):
    '''
    检查更新结果，获取
    '''
    if restart == "yes":
        status,out,err = sshObj.cmd("grep 'update succ! result version:' %s/update_%s.log"%(remoteLogDir,server))
    else:
        status,out,err = sshObj.cmd("grep 'EXECUTE SUCCESSFULL!' %s/update_%s.log"%(remoteLogDir,server))
    if status != 0:
        _,errOut,_ = sshObj.cmd("grep 'ERROR' %s/update_%s.log"%(remoteLogDir,server))
        #sys.stdout.write("[%s] 更新失败:%s" %(server,errOut))
        state.errorResult[server] = errOut
    else:
        state.result[server] = out
def upload(backendName):
    print "上传后端包..."
    sys.stdout.flush()
    status,out = commands.getstatusoutput("sh  /app/opbin/rundeck/online.backend -t %s -g %s"%(backendName,state.game))
    print out
    sys.stdout.flush()
    if status != 0 :
        print "ERROR: 上传后端包失败!"
        sys.exit(1)
def resourceFileCheck(resourceDir,file):
    if not os.path.exists("/app/online/%s/update/%s/%s"%(state.game,resourceDir,file)):
        raise Exception("/app/online/%s/%s/%s 不存在ftp中，请确认!"%(state.game,resourceDir,file))
def getListFile(con):
    l = []
    if not null(con):
        for line in con.split("|"):
            for line1 in line.split("\n"):
                if line1.find("="):
                    s = line1.split("=",1)
                    l.append([s[0].strip(),s[1].strip()])
    return l
def needFileCheck(resourceDir,con):
    if not null(con):
        for i in getListFile(con):
            oldfile = i[0]
            resourceFile = i[1]
            if oldfile.strip() == "":
                print "ERROR: old file can not be empty!Con: " + con
                sys.exit(1)
            resourceFileCheck(resourceDir,resourceFile)
def update(sqlOrNot,sqlFile,backendUpload,backendChangeOrNot,backendName,executeVersionList,restart,resourceDir,replaceFile,addFile,addContent,specialScript,specialScriptExecuteFirst):
    global wwwSsh,remoteShellPath,updateScript,updateScriptPath,remoteWorkDir,remoteLogDir
    updateScriptPath = os.path.abspath(os.path.dirname(__file__))
    updateScript = "updateOnServer.py"
    remoteShellPath = mainOption("clientrootdir").replace("${game}",state.options.game).strip()
    remoteLogDir = remoteShellPath + "/logs"
    nowTimeStr = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    remoteWorkDir = "update_" + nowTimeStr
    print "远端工作目录: " + remoteWorkDir
    sys.stdout.flush()
    www_header = gameOption("www_header")
    www_ip = gameOption("www_ip")
    www_port = gameOption("www_port")
    wwwSsh = ssh.ssh(www_ip)
    versionTag = gameOption("versionTag")
    specialScriptFileName = None
    if not null(specialScript):
        specialScriptFileName = os.path.basename(specialScript)
    haveFileDownload = False
    nullCheck(restart,"必须指定是否重启")
    remoteResourceDir = None
    changeBackendName = None
    needFileCheck(resourceDir,replaceFile)
    needFileCheck(resourceDir,addFile)
    needFileCheck(resourceDir,addContent)
    if sqlOrNot == "yes":
        nullCheck(sqlFile,"sql文件名称必须给出")
        resourceFileCheck(resourceDir,sqlFile)
    if backendChangeOrNot == "yes" or backendUpload == "yes":
        nullCheck(backendName,"后端名称需要给出")
    if backendChangeOrNot == "yes":
        changeBackendName = "-".join(backendName.split("-")[0:3])
    if not null(specialScript):
        if specialScriptExecuteFirst not in ["yes","no"]:
            print "ERROR: 必须指定特殊脚本执行顺序!yes:停服后即执行!no:更新完之后执行特殊脚本!现在的值为: " + specialScriptExecuteFirst
            sys.exit(1)
    if sqlOrNot == "yes" or not null(replaceFile) or not null(addFile) or not null(addContent) or not null(specialScript):
        nullCheck(resourceDir,"资源目录必须指定") 
        remoteResourceDir = resourceDir.strip() + "_" + nowTimeStr
        nullCheck(executeVersionList,"必须给出需要更新的版本")
        nullCheck(www_header,"www_header必须配置")
        nullCheck(www_ip,"www_ip必须配置")
        nullCheck(www_port,"www_port必须配置")
        www_root = gameOption("www_root")
        print "上传文件到资源服务器..."
        sys.stdout.flush()
        resourceToWww(resourceDir,www_root,specialScript,remoteResourceDir)
        print "上传文件到资源服务器完毕!"
        print "资源服务器目录为:" + remoteResourceDir
        sys.stdout.flush()
    #判断是否需要上传后端包
    if backendUpload == "yes":
        upload(backendName)
    #多线程，执行更新前的准备
    #serverlist = getserverlist()
    #serverlist = [["feiliuapp_10010","10.6.197.215"],["feiliu_99999","10.6.197.215"]]
    serverlist = [["feiliuapp_9999","10.6.197.167"]]
    distinctServer = list(set([i[1] for i in serverlist]))
    state.servers = distinctServer
    state.ignoreErrorHost = True
    ccthread.run(scriptDeploy)
    if len(state.errorResult) > 0 or len(state.errorHost) > 0:
        raise Exception( "更新脚本md5检查及目录检查失败,更新失败!" )
    #执行更新操作
    state.servers = serverlist
    print "--------------------------开始更新---------------------------------"
    sys.stdout.flush()
    ccthread.run(executeUpdate,sqlOrNot,sqlFile,backendChangeOrNot,changeBackendName,executeVersionList,restart,www_header,www_ip,www_port,replaceFile,addFile,addContent,specialScriptExecuteFirst,versionTag,specialScriptFileName,remoteResourceDir)
    print "更新命令发送完毕！等待更新结果 ..."
    sys.stdout.flush()
    time.sleep(160)
    #开始检查更新结果
    print "--------------------------开始检查结果----------------------------"
    sys.stdout.flush()
    ccthread.run(checkUpdateResult,restart)
    if len(state.errorHost) > 0:
        print "ERROR:错误主机:\n" + str(state.errorHost)
        sys.stdout.flush()
    else:
        print "没有错误主机!"
    if len(state.errorResult) > 0:
        print "ERROR:更新失败服务器:\n" + str(state.errorResult.keys())
        sys.stdout.flush()
    else:
        print "没有更新失败服务器!"
    print "IMPORTANT: 请生成新的模板信息!!!!!!!!!!!!"
    print "IMPORTANT: 请更新跨服gw跟match服务器!!!!!!!!!!!!"
