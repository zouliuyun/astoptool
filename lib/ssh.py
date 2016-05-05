#!/usr/bin/env python
#-*- coding:utf8 -*-

import paramiko,sys,time
import scp
import state

from arg import *
class ssh:
    def __init__(self,ip,port=22,user="astd",closegw=False):
        self.ip = ip
        self.port = port
        self.user = user
        self.closegw = closegw
        self.gateway = None
        self.gateway_user = None
        self.gateway_port = None
        self.printprogress = None
        try:
            gateway = gameOption("gateway",default="")
        except:
            gateway = ""
        if gateway != "":
            self.gateway = gateway
            self.gateway_user = gameOption("gateway_user",default="astd")
            self.gateway_port = gameOption("gateway_port",type="int",default=22)
        self.gw = None
        self.connect()
    def gw_init(self,cache=True):
        if cache:
            connect = False
            key = getKey(self.gateway_user,self.gateway,self.gateway_port)
            if state.gw_lock.acquire():
                if key not in state.have_connectCache:
                    connect = True
                    state.have_connectCache.append(key)
            state.gw_lock.release()
            self.gw = self.__connect(connect,self.gateway,self.gateway_port,self.gateway_user)
            #print "use gw %s...."%self.gateway
        else:
            #print "direct gw %s...."%self.gateway
            self.gw = self._connect(self.gateway,self.gateway_port,self.gateway_user,None)
    def gw_chan(self):
        if self.gw == None:
            self.gw_init()
        try:
            gw_channel = self.gw.get_transport().open_channel("direct-tcpip",(self.ip,int(self.port)),('',0))
        except:
            print "WARNNING: reconnect gw..."
            self.gw_init(cache=False)
            gw_channel = self.gw.get_transport().open_channel("direct-tcpip",(self.ip,int(self.port)),('',0))
        return gw_channel
    def connect(self,cache=True):
        sock = None
        if not self.closegw:
            if self.gateway != self.ip:
                if not self.gateway or self.gateway.strip() == "":
                    sock = None
                else:
                    sock = self.gw_chan()
        if cache:
            connect = False
            key = getKey(self.user,self.ip,self.port)
            if state.ip_lock.acquire():
                if key not in state.have_connectCache:
                    connect = True
                    state.have_connectCache.append(key)
            state.ip_lock.release()
            self.sshClient = self.__connect(connect,self.ip,self.port,self.user,sock)
        else:
            self.sshClient = self._connect(self.ip,self.port,self.user,sock)
    def __connect(self,connect,ip,port,user,sock=None):
        key = getKey(user,ip,port)
        if connect:
            try:
                sshClient = self._connect(ip,port,user,sock)
                #self.sshClient = sshClient
                state.connectionCaches[key] = sshClient
                return sshClient
            except Exception,e:
                state.errorHost.append(key)
                raise e
        else:
            for i in range(200):
                if key in state.connectionCaches:
                    #self.sshClient = state.connectionCaches[key]
                    sshClient = state.connectionCaches[key]
                    return sshClient
                elif key in state.errorHost:
                    raise Exception("ERROR: connect ip %s failed!"%key)
                else:
                    #print "%s wait ...."%key
                    time.sleep(0.1)
    def _connect(self,ip,port,user,sock=None):
        sshClient = paramiko.SSHClient()
        sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        tries = 0
        sshtry = state.sshtry
        sshTimeOut = state.sshTimeOut
        while True:
            try:
                tries += 1
                sshClient.connect(ip,int(port),user,timeout=sshTimeOut,sock=sock,key_filename=["/home/astd/.ssh/authorized_keys","/home/astd/.ssh/id_rsa"])
                sshClient = sshClient
                return sshClient
            except paramiko.BadHostKeyException, e:
                raise NetworkError("Host key for %s did not match pre-existing key! Server's key was changed recently, or possible man-in-the-middle attack." % ip, e)
            except (
                paramiko.AuthenticationException,
                paramiko.PasswordRequiredException,
                paramiko.SSHException
            ), e:
                msg = str(e)
                #if e.__class__ is paramiko.SSHException and msg == 'Error reading SSH protocol banner':
                if e.__class__ is paramiko.SSHException and msg.startswith('Error reading SSH protocol banner'):
                    #print "WARNNING: reconnect ip:%s %s"%(self.ip,msg)
                    if tries < sshtry:
                        time.sleep(1)
                        continue
                    else:
                        raise Exception(e)
                else:
                    raise Exception(e)
            except Exception,e:
                if str(e) == "timed out" and tries < sshtry:
                    #print "Warnning %s:%s,retries ..."%(ip,str(e))
                    time.sleep(1)
                    continue
                raise e
        
    def cmd(self,cmd):
        try: 
            transport = self.sshClient.get_transport()
            chan = transport.open_session()
        except paramiko.ssh_exception.SSHException,e1:
            #print "Warging :get channel failed!Reconnect server!error info:",str(e1)
            self.connect(cache=False)
            transport = self.sshClient.get_transport()
            chan = transport.open_session()
        chan.exec_command(cmd)
        buff_size = 4096
        #stdin = chan.makefile("wb",buff_size)
        stdout = chan.makefile("r",buff_size)
        stderr = chan.makefile_stderr("r",buff_size)
        status = chan.recv_exit_status()
        return status,stdout.read(),stderr.read()
        #status = None
        #stdout = ""
        #stderr = ""
        #buff_size = 1024
        #while not chan.exit_status_ready():
        #    if chan.recv_ready():
        #        stdout += chan.recv(buff_size)

        #    if chan.recv_stderr_ready():
        #        stderr += chan.recv_stderr(buff_size)

        #exit_status = chan.recv_exit_status()
        ## Need to gobble up any remaining output after program terminates...
        #while chan.recv_ready():
        #    stdout += chan.recv(buff_size)

        #while chan.recv_stderr_ready():
        #    stderr += chan.recv_stderr(buff_size)
        #status = chan.recv_exit_status()
        #chan.close()
        #return (status,stdout,stderr)
    def exitcmd(self,cmdStr):
        status,stdout,err = self.cmd(cmdStr)
        sys.stdout.write("[%s]\n%s"%(cmdStr,stdout))
        sys.stdout.flush()
        if status != 0:
            raise Exception(err)
        return stdout
    def scpprogress(self,filename,size,sent):
        now = time.time()
        #if int(now) % 5 == 0 and now % 1 < 0.1:
        sys.stdout.write('\r')
        if size > 1024 * 1024:
            sys.stdout.write("文件名:%s,已传输:%dMB,总共大小:%dMB,已传输:%.2f%%"%(filename,float(sent)/1024.0/1024.0,float(size)/1024.0/1024.0,float(sent)/size*100))
        elif size > 1024:
            sys.stdout.write("文件名:%s,已传输:%dKB,总共大小:%dKB,已传输:%.2f%%"%(filename,float(sent)/1024.0,float(size)/1024.0,float(sent)/size*100))
        else:
            sys.stdout.write("文件名:%s,已传输:%dB,总共大小:%dB,已传输:%.2f%%"%(filename,sent,size,float(sent)/size*100))
        sys.stdout.flush()
        pass
    def setprogress(self,value):
        self.printprogress = value
    def testput(self,*args,**kwargs):
        self.getScp(0.1).put(*args,**kwargs)
    def put(self,*args,**kwargs):
        sshtry = state.sshtry
        err = None
        for i in range(sshtry):
            try:
                self.getScp().put(*args,**kwargs)
                break
            except paramiko.ChannelException,ce:
                err = ce
                print "Warnning: ChannelException",str(ce),"retry ..."
                continue
            except Exception,e:
                err = e
                if str(e).find("Unable to open channel") >= 0:
                    print "Warnning:",str(e),"retry ..."
                    continue
                raise e
        else:
            raise err
    def get(self,*args,**kwargs):
        sshtry = state.sshtry
        err = None
        for i in range(sshtry):
            try:
                self.getScp().get(*args,**kwargs)
                break
            except paramiko.ChannelException,ce:
                err = ce
                print "Warnning: ChannelException",str(ce),"retry ..."
                continue
            except Exception,e:
                err = e
                if str(e).find("Unable to open channel") >= 0:
                    print "Warnning:",str(e),"retry ..."
                    continue
                raise e
        else:
            raise err
    def _getScp(self,scptimeout=5.0):
        transport = self.sshClient.get_transport()
        if not self.printprogress:
            scpClient = scp.SCPClient(transport,socket_timeout=scptimeout)
        else:
            scpClient = scp.SCPClient(transport,progress=self.scpprogress,socket_timeout=scptimeout)
        return scpClient
    def getScp(self,scptimeout=5.0):
        try:
            scpClient = self._getScp(scptimeout)
        except paramiko.ssh_exception.SSHException,e1:
            print "Warging :get scp failed!Reconnect server!error info:",str(e1)
            self.connect(cache=False)
            scpClient = self._getScp(scptimeout)
        return scpClient
    def getssh(self):
        return self.sshClient
if __name__ == "__main__":
    #s = ssh("gcld_kbm",22222)
    state.game = "gcld"
    state.language = "test"
    s = ssh("10.37.48.31")
    #s = ssh("10.6.197.215")
    #s = ssh("gcld_kbm",port=22222)
    print s.cmd("/sbin/ifconfig")
    print s.cmd("whoami")
    print s.cmd("whoami")
    print s.cmd("whoami")
    print s.cmd("whoami")
    print s.cmd("whoami")
    s.put("xxxx")
