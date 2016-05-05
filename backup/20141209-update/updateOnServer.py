#!/usr/bin/env python
#-*- coding:utf8 -*-
import sys,os,json,commands,re,time,hashlib
import optparse

def null(Str):
    if Str == None or str(Str).strip() == "" or str(Str).lower().strip() == "null" or str(Str).lower().strip() == "none":
        return True
    else:
        return False
def nullCheck(str,msg):
    if null(str):
        print "ERROR: " + msg
        sys.exit(1)
def argInit():
    parser = optparse.OptionParser()
    parser.add_option("-g","--game",dest="game",help="game name")
    parser.add_option("-s","--server",dest="server",help="server name")
    parser.add_option("-q","--sqlOrNot",dest="sqlOrNot",type="choice",choices=["yes","no"],help="execute sql or not")
    parser.add_option("-Q","--sqlFile",dest="sqlFile",help="if execute sql,give the sql file name")
    parser.add_option("-b","--backendChangeOrNot",dest="backendChangeOrNot",type="choice",choices=["yes","no"],help="change backend path or not")
    parser.add_option("-B","--backendName",dest="backendName",help="if change backend path,give the backend name")
    parser.add_option("-v","--executeVersionList",dest="executeVersionList",help="need update version list")
    parser.add_option("-R","--restart",dest="restart",type="choice",choices=["yes","no"],help="need restart server or not")
    parser.add_option("-H","--www_header",dest="www_header",help="www header")
    parser.add_option("-i","--www_ip",dest="www_ip",help="www ip")
    parser.add_option("-p","--www_port",dest="www_port",help="www port")
    parser.add_option("-d","--resourceDir",dest="resourceDir",help="resource dir")
    parser.add_option("-r","--replaceFile",dest="replaceFile",help="replace file list,eg:backend/apps/job.properties=job.properties|...")
    parser.add_option("-a","--addFile",dest="addFile",help="add file list,eg:backend/apps/=job.properties|...")
    parser.add_option("-c","--addContent",dest="addContent",help="add content file list,eg:backend/apps/job.properties=add_job.properties|...")
    parser.add_option("-o","--specialScript",dest="specialScript",help="need some special exceute.")
    parser.add_option("-O","--specialScriptExecuteFirst",dest="specialScriptExecuteFirst",type="choice",choices=["yes","no"],help="execute special script at first,or will execute at last.")
    parser.add_option("-D","--workdir",dest="workdir",help="work dir.")
    parser.add_option("-V","--versionTag",dest="versionTag",help="get version the tag.")

    global options,haveFileDownload,yx,executeDir,backdir
    haveFileDownload = False
    (options, args) = parser.parse_args()
    nullCheck(options.game,"game must be given")
    nullCheck(options.versionTag,"versionTag must be given")
    nullCheck(options.restart,"restart or not must be given")
    if options.sqlOrNot == "yes":
        nullCheck(options.sqlFile,"sql file must be given")
    if options.sqlOrNot == "yes" or not null(options.replaceFile) or not null(options.addFile) or not null(options.addContent) or not null(options.specialScript):
        haveFileDownload = True
        nullCheck(options.resourceDir,"resource dir must be given")
        nullCheck(options.www_header,"www_header must be given")
        nullCheck(options.www_ip,"www_ip must be given")
        nullCheck(options.www_port,"www_port must be given")
    if not os.path.exists("/app/%s_%s"%(options.game,options.server)):
        print "ERROR: game dir not exists"
        sys.exit(1)
    if not null(options.specialScript):
        if options.specialScriptExecuteFirst not in ["yes","no"]:
            print "ERROR: will execute special script ,but not define specialScriptExecuteFirst varaiable as yes or no! It is: " + options.specialScriptExecuteFirst
            sys.exit(1)
    yx = options.server.split("_")[0]
def cmd(cmdStr):
    status,output = commands.getstatusoutput(cmdStr)
    if status != 0 :
        print "ERROR: [%s] execute failed!\nOutput:%s"%(cmdStr,output)
        sys.exit(1)
    return output
def calMd5(filepath):
    with open(filepath,'rb') as f:
        md5obj = hashlib.md5()
        md5obj.update(f.read())
        hash = md5obj.hexdigest()
        return hash
def md5Check(filename):
    filemd5 = cmd("grep ' %s$' md5.txt|awk '{print $1}'"%filename)
    localmd5 = calMd5(filename)
    if filemd5.strip() != localmd5:
        print "ERROR: %s md5 check fail"%filename
        sys.exit(1)
def download(file):
    filename = os.path.basename(file)
    if os.path.exists(filename):
        cmd("rm -f filename")
    cmd("wget -q --header='host:%s' http://%s:%s/%s/update/%s/%s"%(options.www_header,options.www_ip,options.www_port,options.game,options.resourceDir,file))
    if file != "md5.txt":
        md5Check(filename)
def getListFile(con):
    l = []
    if not null(con):
        for line in con.split("|"):
            for line1 in line.split("\n"):
                if line1.find("="):
                    s = line1.split("=",1)
                    l.append([s[0].strip(),s[1].strip()])
    return l
def getNeedFile(con):
    for i in getListFile(con):
        oldfile = i[0]
        if oldfile.strip() == "":
            print "ERROR: old file can not be empty"
            sys.exit(1)
        elif not os.path.exists("/app/%s_%s/%s"%(options.game,options.server,oldfile)):
            print "ERROR: [/app/%s_%s/%s] not exists"%(options.game,options.server,oldfile)
            sys.exit(1)
        else:
            abspath = os.path.abspath("/app/%s_%s/%s"%(options.game,options.server,oldfile))
            if abspath.find("/app/%s_%s/"%(options.game,options.server)) < 0:
                print "ERROR: abspath is not the game dir! is: " + abspath
                sys.exit(1)
        download(i[1])
def getFile():
    if haveFileDownload:
        download("md5.txt")
        if options.sqlOrNot == "yes":
            download(options.sqlFile)
        if not null(options.specialScript):
            download(options.specialScript)
        getNeedFile(options.replaceFile)
        getNeedFile(options.addFile)
        getNeedFile(options.addContent)
def getVersion():
    url = os.popen("grep -E 'game.url\s*=' /app/%s_%s/backend/apps/%s.properties | grep -Ev '^\s*#' | head -1 | cut -d'=' -f2 | xargs echo"%(options.game,options.server,yx)).read().strip()
    domain = re.match(r'https?://?([^/]*).*',url)
    if not domain:
        print "ERROR: url get failed"
        return None
    host = domain.groups()[0].strip()
    version = os.popen("curl -s -H 'host:%s' %s/root/gateway.action?command=version"%(host,url.replace(host,"127.0.0.1"))).read()
    if re.search(options.versionTag,version):
        return json.loads(version)[options.versionTag]
    else:
        return None
def versionCheck():
    curVersion = getVersion()
    versionCheck = False
    if curVersion == None :
        print "ERROR: get version faield"
        sys.exit(1)
    else:
        s = options.executeVersionList.split(",")
        for v in s:
            if v.strip() == curVersion:
                versionCheck = True
                break
    return versionCheck
def backendChangeCheck():
    global oldBackendName
    oldBackendName = None
    if options.backendChangeOrNot == "yes":
        if not re.match(r'^%s_[^/]*$'%options.game,options.backendName):
            print "ERROR: new backend name [%s] not match %s_.* backend name"%(options.backendName,options.game)
            sys.exit(1)
        #nullCheck(options.backendName,"new backend name must be given")
        oldBackendName = cmd("grep '^jar.path' /app/%s_%s/backend/apps/app.properties | cut -d',' -f1| cut -d'/' -f5"%(options.game,options.server))
        if not re.match(r'^%s_[^/]*$'%options.game,oldBackendName):
            print "ERROR: old backend name [%s] not match %s_.* backend name"%(oldBackendName,options.game)
            sys.exit(1)
def stopProcess():
    pid = cmd("ps x | grep '/usr/local/jdk/bin/java.*/app/%s_%s/' | grep -v grep | awk '{print $1}'"%(options.game,options.server))
    print "the pid is : " + pid
    print "stop the process ..."
    sys.stdout.flush()
    if pid.strip() != "":
        cmd("kill -9 " + pid)
def startProcess():
    print "start the game ..."
    sys.stdout.flush()
    cmd("export JAVA_HOME=/usr/local/jdk; export LC_ALL='en_US.UTF-8'; export LANG='en_US.UTF-8'; source /etc/profile; sh /app/%s_%s/backend/bin/startup.sh start"%(options.game,options.server))
    version = None
    for i in range(30):
        version = getVersion()
        if version != None:
            break
        else:
            time.sleep(5)
    return version
def sqlUpdate():
    print "start backup database..."
    sys.stdout.flush()
    cmd("pandora --dump -R --opt %s_%s > %s/%s_%s.sql"%(options.game,options.server,backdir,options.game,options.server))
    cmd("dos2unix " + options.sqlFile)
    print "update database..."
    sys.stdout.flush()
    cmd("pandora --update %s_%s < %s" %(options.game,options.server,options.sqlFile))
    print "finish update database"
    sys.stdout.flush()
def backendUpdate():
    print "start backup app.properties and plugins.xml file..."
    sys.stdout.flush()
    cmd("cp /app/%s_%s/backend/apps/app.properties %s/"%(options.game,options.server,backdir))
    cmd("cp /app/%s_%s/backend/apps/plugins.xml %s/"%(options.game,options.server,backdir))
    print "start update jar load file app.properties and plugins.xml..."
    sys.stdout.flush()
    cmd("sed -i 's/%s/%s/g' /app/%s_%s/backend/apps/app.properties"%(oldBackendName,options.backendName,options.game,options.server))
    cmd("sed -i 's/%s/%s/g' /app/%s_%s/backend/apps/plugins.xml"%(oldBackendName,options.backendName,options.game,options.server))
    print "app.properties and plugins.xml update finished!"
    sys.stdout.flush()
def replcaceFile():
    for i in getListFile(options.replaceFile):
        newfilename = i[1]
        oldfile = i[0]
        filepath = os.path.dirname(oldfile)
        print "backup file %s ..." %oldfile
        sys.stdout.flush()
        cmd("cp /app/%s_%s/%s %s/"%(options.game,options.server,oldfile,backdir))
        print "replace file %s ..." %newfilename
        sys.stdout.flush()
        cmd("cp %s /app/%s_%s/%s"%(newfilename,options.game,options.server,oldfile))
def addFile():
    for i in getListFile(options.addFile):
        newfilename = i[1]
        filepath = i[0]
        if os.path.exists("/app/%s_%s/%s/%s"%(options.game,options.server,filepath,newfilename)):
            print "Warning: backup file %s ..." %newfilename
            sys.stdout.flush()
            cmd("cp /app/%s_%s/%s/%s %s/"%(options.game,options.server,filepath,newfilename,backdir))
        print "add file %s ..." %newfilename
        sys.stdout.flush()
        cmd("cp %s /app/%s_%s/%s/"%(newfilename,options.game,options.server,filepath))
def addContent():
    for i in getListFile(options.addContent):
        addfilename = i[1]
        oldfile = i[0]
        print "backup file %s ..." %oldfile
        sys.stdout.flush()
        cmd("cp /app/%s_%s/%s %s/"%(options.game,options.server,oldfile,backdir))
        print "add file %s content..." %addfilename
        sys.stdout.flush()
        cmd("sed -i '$r%s' /app/%s_%s/%s"%(addfilename,options.game,options.server,oldfile))
if __name__ == "__main__":
    argInit()
    #backend need change dir or not
    backendChangeCheck()
    #create work dir
    if haveFileDownload or options.backendChangeOrNot == "yes":
        nullCheck(options.executeVersionList,"update version list must be given")
        #check the version need update or not
        if not versionCheck():
            print "ERROR: the version is not need update"
            sys.exit(1)
        if null(options.workdir):
            print "ERROR: workdir must be given"
            sys.exit(1)
        executeDir = "/app/opbin/update/%s/%s/%s"%(options.game,options.workdir,options.server)
        if not os.path.exists(executeDir):
            os.makedirs(executeDir)
        os.chdir(executeDir)
        backdir = "updateBackupDir"
        if os.path.exists(backdir):
            print "ERROR: %s dir have exists" %backdir
            sys.exit(1)
        os.mkdir(backdir)
    #download the need file
    getFile()
    if options.restart == "yes":
        stopProcess()
    #if have special script and at first execute,then execute the special script first
    if not null(options.specialScript) and options.specialScriptExecuteFirst == "yes":
        print "start execute special script at first:" + "sh %s -g %s -s %s -i %s -h %s -p %s -d %s"%(options.specialScript,options.game,options.server,options.www_ip,options.www_header,options.www_port,options.resourceDir)
        sys.stdout.flush()
        cmd("sh %s -g %s -s %s -i %s -h %s -p %s -d %s"%(options.specialScript,options.game,options.server,options.www_ip,options.www_header,options.www_port,options.resourceDir))
    if options.sqlOrNot == "yes":
        sqlUpdate()
    if options.backendChangeOrNot == "yes":
        backendUpdate()
    replcaceFile()
    addFile()
    addContent()
    #if have special script and at end execute,then execute the special script first
    if not null(options.specialScript) and options.specialScriptExecuteFirst == "no":
        print "start execute special script at end:" + "sh %s -g %s -s %s -i %s -h %s -p %s -d %s"%(options.specialScript,options.game,options.server,options.www_ip,options.www_header,options.www_port,options.resourceDir)
        sys.stdout.flush()
        cmd("sh %s -g %s -s %s -i %s -h %s -p %s -d %s"%(options.specialScript,options.game,options.server,options.www_ip,options.www_header,options.www_port,options.resourceDir))
    if options.restart == "yes":
        version = startProcess()
        if version == None:
            print "ERROR: start fail"
            sys.exit(1)
        else:
            print "update succ! result version: " + version
            print "start succ"
            sys.stdout.flush()
    print "EXECUTE SUCCESSFULL!"
