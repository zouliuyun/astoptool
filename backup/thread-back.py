#!/usr/bin/env python
#-*- coding:utf8 -*-

import threading,Queue
import time,json,os
import ssh

global threadingCount
threadingCount = 40

def execThread(sshObj,cmd,result,ip):
    result[ip] = sshObj.cmd(cmd)
    #print "cmd theading count:%d"%threading.activeCount()
#def putThread(sshObj,file,remote_path='.',recursive=False, preserve_times=False):
def execCmd(sshObj,ip,game):
    #print sshObj.cmd("ps x|grep %s|grep -v grep"%game)
    result = sshObj.cmd("ps x|grep %s|grep -v grep"%game)
    print "[%s] %s" %(game,result[1])
def putThread(sshObj,*args,**kwargs):
    sshObj.put(*args,**kwargs)
def sshConn(ip,servers):
    check = False
    for i in range(10):
        try:
            servers[ip] = ssh.ssh(ip)
            check = True
            break
        except:
            time.sleep(1)
            print "connect server %s try again ..."%ip
    if not check:
        print "connect server %s failed!"%ip
    #print "ssh theading count:%d"%threading.activeCount()
def sshThread(iplist):
    servers = {}
    threads = []
    for ip in list(set(iplist)):
        server = {}
        r = threading.Thread(target=sshConn,kwargs={"ip":ip,"servers":servers})
        threads.append(r)
    runthreadsQueue = Queue.Queue()
    for thread in threads:
        if runthreadsQueue.qsize() > threadingCount:
            thread1 = runthreadsQueue.get()
            thread1.join()
        runthreadsQueue.put(thread)
        thread.start()
        #print "ssh queue size:%d"%runthreadsQueue.qsize()
    for thread in threads:
        thread.join()
    for ip in iplist:
        if ip not in servers:
            raise Exception("have server %s connet ssh failed!"%ip)
    print "server count :%d"%len(servers)
    return servers
def threadFunc(func,sshServers,gameServers,*args,**kwargs):
    result = {}
    threads = []
    for row in gameServers:
        game = row[0]
        serverIp = row[1]
        r = threading.Thread(target=func,args=(sshServers[serverIp],serverIp,game).__add__(args),kwargs=(kwargs))
        threads.append(r)
    runthreadsQueue = Queue.Queue()
    for thread in threads:
        if runthreadsQueue.qsize() > threadingCount:
            thread1 = runthreadsQueue.get()
            thread1.join()
        runthreadsQueue.put(thread)
        thread.start()
    for thread in threads:
        thread.join()
    return result
def threadCmd(sshServers,gameServers,cmd):
    result = {}
    threads = []
    for row in gameServers:
        game = row[0]
        serverIp = row[1]
        r = threading.Thread(target=execThread,args=(sshServers[serverIp],cmd.replace("${flag}",game),result,game))
        threads.append(r)
    runthreadsQueue = Queue.Queue()
    for thread in threads:
        if runthreadsQueue.qsize() > threadingCount:
            thread1 = runthreadsQueue.get()
            thread1.join()
        runthreadsQueue.put(thread)
        thread.start()
    for thread in threads:
        thread.join()
    return result
#def threadPut(sshServers,gameServers,file,remote_path='.',recursive=False, preserve_times=False):
def threadPut(sshServers,gameServers,*args,**kwargs):
    result = {}
    threads = []
    for row in gameServers:
        game = row[0]
        serverIp = row[1]
        r = threading.Thread(target=putThread,args=(sshServers[serverIp],).__add__(args),kwargs=(kwargs))
        threads.append(r)
    runthreadsQueue = Queue.Queue()
    for thread in threads:
        if runthreadsQueue.qsize() > threadingCount:
            thread1 = runthreadsQueue.get()
            thread1.join()
        runthreadsQueue.put(thread)
        thread.start()
    for thread in threads:
        thread.join()
    return result
def multiRun(gameServers,sshServers):
    def multi(func):
        def decorator(*args,**kwargs):
            for row in gameServers:
                game = row[0]
                ip = row[1]
                print args
                print kwargs
                func(*args,**kwargs)
        return decorator
    return multi
def getUniqServer(servers):
    uniqServers = []
    for i in servers:
        if i[1] not in uniqServers:
            uniqServers.append(i[1])
    return uniqServers
if __name__ == "__main__" :
    s = os.popen("python ../main.py -a serverlist -g gcmob -l cn").read()
    gameServers = json.loads(s)
    #gameServers = [["feiliu_100002","10.6.197.215"],["feiliu_100003","10.6.197.215"]]
    uniqServers = getUniqServer(gameServers)

    #print "time start:" , time.time()
    sshServers = sshThread(uniqServers)
    #print "ssh finish:" , time.time()
    #r1 = threadCmd(sshServers,gameServers,"ps x| grep ${flag}|grep -v grep")
    #r1 = threadCmd(sshServers,gameServers,"ps x")
    r1 = threadFunc(execCmd,sshServers,gameServers)
    #r1 = threadCmd(sshServers,gameServers,"echo a")
    #for server in r1:
    #    print server,r1[server]

    #r1 = threadPut(sshServers,gameServers,"scp.py",remote_path="/tmp/")
    #print "cmd1:" , time.time()
    #@multiRun(gameServers,sshServers)
    #def test(*args,**kwargs):
    #    print "#########"
    #    print args
    #    print kwargs
    #test(1,2,a=1)
