# -*- coding: utf-8 -*-
"""
两台线上服之间传输文件
Example:

    files = ['/app/opbak/tjmob_37wan_1_0406.sql']
    
    server1 = '120.132.61.36' #ip for ssh
    server2 = '10.6.196.32'   #ip for ssh

    dest_dir = '/app/opbak/xiaoyu_test1'
    uploader1 = Uploader(source_ip=server1, target_ip=server2)
    uploader1._debug = True
    uploader1.transfer(files, dest_dir)


2015-05-13 Xiaoyu Created
"""

from fabric.api import env, run, local, execute, quiet, hosts, cd, settings, hide
from contextlib import contextmanager
import os
import random
import string

from bible.utils import WGET, TIMESTAMP, RSYNC

########################################
#class Uploader
def mk_remote_dir(remote_dir):
    run(' [ -d {0} ] || mkdir -p {0} '.format(remote_dir))

def remote_dir_exists(dir):
    with quiet():
        dir_exists = run('test -d {}'.format(dir)).succeeded
    return dir_exists

def reload_nginx():
    run('sudo /app/nginx/sbin/nginx -t')
    run('sudo /sbin/service nginx reload')

def random_string(N):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(N))

@contextmanager
def setting_trans_env(server_name):
    conf_name = 'download_{}.conf'.format(server_name)
    root_dir = '/app/opbak/download_{}_{}'.format(TIMESTAMP, server_name)
    mk_remote_dir(root_dir)

    try:
        with cd('/app/nginx/conf/vhost'):
            run('''echo -e "server {\\n    listen       80;\\n    server_name  %s;\\n    root %s;\\n    index Main.html;\\n    access_log  logs/default.access.log  main;\\n    location / {\\n        expires 0;\\n    }\\n\\n    error_page  404 500 502 503 504  /404.html;\\n}" >%s''' % (server_name, root_dir, conf_name))

        reload_nginx()

        yield

    finally:
        with cd('/app/nginx/conf/vhost'):
            run('rm -f {}'.format(conf_name))
        reload_nginx()
        run('rm -rf {}'.format(root_dir))

def get_external_ip(int_ip):
    
    @hosts(int_ip)
    def _get_external_ip():
            ext_ip =  run('''curl -s ip.cn |awk '{split($2,x,"：");print x[2]}' ''')
            return ext_ip

    ret_value = execute(_get_external_ip)[int_ip]

    return ret_value

def file_exists_check(file):
    with quiet():
        ret = run('test -f {}'.format(file)).succeeded
    return ret

def retrieve_file_names(files):
    """
    返回文件名字，同时检查是否有重复文件名，文件是否都存在
    Uploader 类不支持文件中有重复文件名，会由此引发问题。
    """
    filenames = [os.path.basename(each) for each in files]

    for each_file in files:
        if not file_exists_check:
            raise Exception("File {} doesn't exist on {}".format(each_file, env.host_string)) 
    
    if len(set(filenames)) != len(files):
        raise Exception('Duplicate file names in the files: {}'.format(files))

    return filenames

class Uploader(object):
    """
    两台线上服之间传输文件的基础类
    
    Example:

        files = ['/app/opbak/tjmob_37wan_1_0406.sql']
        
        server1 = '120.132.61.36' #ip for ssh
        server2 = '10.6.196.32'   #ip for ssh
        dest_dir = '/app/opbak/xiaoyu_test1'
        uploader1 = Uploader(source_ip=server1, target_ip=server2)
        uploader1.transfer(files, dest_dir)

    To-do: 
    .. 增加md5校验
    """
    def __init__(self, source_ip, target_ip):
        self.source_ip = source_ip
        self.target_ip = target_ip
        self.server_name = random_string(12)
        self._debug = False

    @property
    def source_ext_ip(self):
        return get_external_ip(self.source_ip)

    def transfer(self, files, dest_dir):

        md5 = {}

        def md5sum(file):
            return run("md5sum %s | awk '{print $1}'" % file)

        def wget_files(filenames, dest_dir):
            mk_remote_dir(dest_dir)
            with cd(dest_dir):
                for each_filename in filenames:
                    #这里有一种极端情况，即使判断了两个ip不一样，仍然有可能是同一台服务器上，此时以md5计算文件值为准。倘若md5相同，则认为是同一个文件，就跳过下载（如果继续下载wget -O会清空文件!!)。希望永远不会走到下面这条判断。
                    file_exits = file_exists_check(each_filename)
                    if file_exits:
                        if md5[each_filename] == md5sum(each_filename):
                            break 

                    run('''{0} -O {1} --header="Host:{2}" http://{3}/{1}'''.format(WGET, each_filename, self.server_name, self.source_ext_ip))

        @hosts(self.source_ip)
        def _transfer(files, dest_dir):
            filenames = retrieve_file_names(files)
            root_dir = '/app/opbak/download_{}_{}'.format(TIMESTAMP, self.server_name)
            with setting_trans_env(self.server_name):
                for each_file in files:
                    filename = os.path.basename(each_file)
                    md5[filename] = md5sum(each_file)
                    with cd(root_dir):
                        run('ln -sf {} {}'.format(each_file, filename))

                execute(wget_files, filenames, dest_dir, hosts=[self.target_ip])

        @hosts(self.source_ip)
        def _copy(files, dest_dir):
            for each_file in files:
                run('{} {} {}/'.format(RSYNC, each_file, dest_dir))

        def _execute_transfer():
            if self.source_ip == self.target_ip:
                execute(_copy, files, dest_dir)
            else:
                execute(_transfer, files, dest_dir)

        if self._debug:
            _execute_transfer()
        else:
            with settings(hide('everything')):
                _execute_transfer()

#End class Uploader
########################################################################



