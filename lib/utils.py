# -*- coding: utf-8 -*-
"""
一些常用的简单通用模块以及全局常量

2015-04-17 Xiaoyu Created
"""

from fabric.api import env, run
import random
import time
import re
import string

#全局常量
TIMESTAMP = '{}_{}'.format(time.strftime("%Y%m%d_%H%M%S"), ''.join(random.choice(string.digits) for _ in range(6)))
RSYNC = 'rsync -aPq -e "ssh -o ConnectionAttempts=10 -o ConnectTimeout=5"'
WGET = 'wget -c -t 10 -T 10 -q'
BZIP2 = 'bzip2 -9 -k'

def set_fabric_common_env():
    """
    设置一些常见的通用的fabric env
    """
    env.user = 'astd'
    env.use_ssh_config = True   # This is important when running under root.
    env.connection_attempts = 5
    env.disable_known_hosts = True
    env.keepalive = 60

def server_filter(gameServers, pattern_include, pattern_exclude='notinclude'):
    print(pattern_include)
    a = [ each for each in gameServers if re.match(pattern_include, each) ]
    b = [ each for each in a if not re.match(pattern_exclude, each) ]
    return b

def random_string(N):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(N))



