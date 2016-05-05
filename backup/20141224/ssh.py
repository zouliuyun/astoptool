#!/usr/bin/env python
#-*- coding:utf8 -*-

import paramiko,sys
import scp
import state

class ssh:
    def __init__(self,ip,port=22,user="astd"):
        self.ip = ip
        self.port = port
        self.user = user
        sshClient = paramiko.SSHClient()
        sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        tries = 0
        sshtry = state.sshtry
        while True:
            try:
                tries += 1
                sshClient.connect(ip,port,user,timeout=5,key_filename=["/home/astd/.ssh/authorized_keys","/home/astd/.ssh/id_rsa"])
                self.sshClient = sshClient
                self.transport = sshClient.get_transport()
                break
            except paramiko.BadHostKeyException, e:
                raise NetworkError("Host key for %s did not match pre-existing key! Server's key was changed recently, or possible man-in-the-middle attack." % ip, e)
            except (
                paramiko.AuthenticationException,
                paramiko.PasswordRequiredException,
                paramiko.SSHException
            ), e:
                msg = str(e)
                if e.__class__ is paramiko.SSHException and msg == 'Error reading SSH protocol banner':
                    if tries < sshtry:
                        continue
                    else:
                        raise Exception(e)
                else:
                    raise Exception(e)
            except Exception,e:
                raise Exception(e)
    def cmd(self,cmd):
        #stdin, stdout, stderr = self.sshClient.exec_command(cmd)
        #stderrStr = stderr.read()
        #if stderrStr.strip() != "":
        #    raise Exception(stderrStr)
        #stdoutStr = stdout.read()
        #return stdoutStr
        chan = self.transport.open_session()
        chan.exec_command(cmd)
        status = None
        stdout = ""
        stderr = ""
        buff_size = 4096
        while not chan.exit_status_ready():
            if chan.recv_ready():
                stdout += chan.recv(buff_size)

            if chan.recv_stderr_ready():
                stderr += chan.recv_stderr(buff_size)

        exit_status = chan.recv_exit_status()
        # Need to gobble up any remaining output after program terminates...
        while chan.recv_ready():
            stdout += chan.recv(buff_size)

        while chan.recv_stderr_ready():
            stderr += chan.recv_stderr(buff_size)
        status = chan.recv_exit_status()
        chan.close()
        return (status,stdout,stderr)
    def put(self,*args,**kwargs):
        #transport = self.sshClient.get_transport()
        transport = self.transport
        scpClient = scp.SCPClient(transport)
        scpClient.put(*args,**kwargs)
    def get(self, *args,**kwargs):
        transport = self.transport
        scpClient = scp.SCPClient(transport)
        scpClient.get(*args,**kwargs)
    def getssh(self):
        return self.sshClient
if __name__ == "__main__":
    #s = ssh("gcld_kbm",22222)
    s = ssh("10.6.197.215")
    print s.cmd("/sbin/ifconfig")
    print s.cmd("whoami")
