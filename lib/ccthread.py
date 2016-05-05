#!/usr/bin/env python
#-*- coding:utf8 -*-

import threading,Queue,multiprocessing
import time,json,os,sys
import ssh
import state
from arg import *

def execCmd(sshObj,ip,game):
    #print sshObj.cmd("ps x|grep %s|grep -v grep"%game)
    result = sshObj.cmd("ps x|grep %s|grep -v grep"%game)
    sys.stdout.write( "[%s] %s" %(game,result[1]) )
def getIpGame(server):
    if isinstance(server,list):
        ip = server[1]
        gamename = server[0]
    else:
        ip = server
        gamename = server
    return ip,gamename
def sshInit():
    runthreadsQueue = Queue.Queue()
    iplist = []
    for server in state.servers:
        #服务器列表中的元素支持["feiliu_1","1.1.1.1"]跟"1.1.1.1"两种类型
        ip,gamename = getIpGame(server)
        key = getKey(state.user,ip,state.port)
        if key not in iplist:
            iplist.append(key)
            r = threading.Thread(target=getSsh,args=(ip,),kwargs=({"port":state.port,"user":state.user}))
            if runthreadsQueue.qsize() > state.sshThreadingCount:
                thread1 = runthreadsQueue.get()
                thread1.join()
            runthreadsQueue.put(r)
            r.start()
    for i in range(runthreadsQueue.qsize()):
        thread1 = runthreadsQueue.get()
        thread1.join()
    if not state.ignoreErrorHost:
        if len(state.errorHost) > 0:
            raise Exception("ERROR: 连接失败服务器如下:\n%s"%(str(state.errorHost)))
    else:
        if len(state.errorHost) > 0:
            sys.stdout.write( "Warning:连接失败服务器如下:\n"  + str(state.errorHost))
    #ssh初始化完毕
    state.sshInit = True
    #print "aa",state.sshInit
def getSsh(ip,port=22,user="astd"):
    return ssh.ssh(ip,port,user)
def run(*args,**kwargs):
    if not state.sshInit:
        #如果忽略连接失败的主机，则使用ssh建立连接跟执行命令同时运行，如果没有找到ssh，则等待，最多等待state.sshTimeOut的时间
        if state.ignoreErrorHost:
            print "建立连接跟执行命令同时开始运行..."
            #sshProcess = multiprocessing.Process(target=sshInit)
            sshProcess = threading.Thread(target=sshInit)
            sshProcess.start()
            #cmdProcess = multiprocessing.Process(target=threadFunc,args=args,kwargs=(kwargs))
            cmdProcess = threading.Thread(target=threadFunc,args=args,kwargs=(kwargs))
            cmdProcess.start()
            sshProcess.join()
            cmdProcess.join()
        else:
            print "先建立连接然后运行命令..."
            sshInit()
            threadFunc(*args,**kwargs)
    else:
        print "直接执行命令..."
        threadFunc(*args,**kwargs)
def threadFunc(func,*args,**kwargs):
    #print func,args,kwargs
    state.result = {}
    state.errorResult = {}
    threads = []
    runthreadsQueue = Queue.Queue()
    curCount = 0
    for server in state.servers:
        ip,gamename = getIpGame(server)
        key = getKey(state.user,ip,state.port)
        #服务器列表中的元素支持["feiliu_1","1.1.1.1"]跟"1.1.1.1"两种类型
        for i in range(state.sshTimeOut * 10):
            if key in state.connectionCaches or key in state.errorHost:
                break
            time.sleep(1 / 10)
        sshobj = None
        try:
            sshobj = getSsh(ip,port=state.port,user=state.user)
        except Exception,e1:
            print "Warning: ssh connect failed! err:%s"%str(e1)
        if not sshobj:
            print "%s服务器连接失败"%ip
            if gamename not in state.errorResult:
                state.errorResult[gamename] = ""
            state.errorResult[gamename] += "\n%s服务器连接失败"%ip
            if state.ignoreErrorHost:
                continue
            else:
                raise Exception("%s服务器连接失败"%ip)
        #print func,sshobj,ip,gamename
        r = threading.Thread(target=func,args=(sshobj,ip,gamename).__add__(args),kwargs=(kwargs))
        #如果队列已满，则等待队列的第一个执行完毕，然后再执行一个新线程加入队列
        if runthreadsQueue.qsize() > state.threadingCount:
            try:
                if state.threadInterval != None and curCount >= state.threadingCount:
                    print "等待%ds后继续并发..."%state.threadInterval
                    time.sleep(int(state.threadInterval))
                    curCount = 0
            except Exception,e10:
                print "state.threadInterval必须为None或者数字！err:%s"%str(e10)
            #print "队列已满",runthreadsQueue.qsize()
            thread1 = runthreadsQueue.get()
            thread1.join()
        #else:
            #print "队列深度为:",runthreadsQueue.qsize()
        curCount += 1
        runthreadsQueue.put(r)
        r.start()
    #等待所有线程执行完毕
    for i in range(runthreadsQueue.qsize()):
        thread = runthreadsQueue.get()
        thread.join()
    #如果设置不忽略错误则需要退出
    if len(state.errorResult) > 0:
        for i in state.errorResult:
            sys.stdout.write( "[%s] ERROR: %s\n" %(i,state.errorResult[i]))
        if not state.ignoreErrorHost:
            raise Exception("当前设置不忽略报错，已退出!")
if __name__ == "__main__" :
    s = os.popen("python ../main.py -a serverlist -g gcmob -l cn").read()
    state.servers = json.loads(s)
    state.ignoreErrorHost = True
    #state.servers = [["feiliu_100002","10.6.197.215"],["feiliu_100003","1.1.1.1"],["feiliu_100003","10.6.197.215"]]
    #state.servers.insert(10,["fei_10","1.1.1.1"])
    run(execCmd)
    #run(execCmd)
