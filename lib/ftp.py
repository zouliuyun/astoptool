# -*- coding: utf-8 -*-
"""

2015-05-13 Xiaoyu Created
"""
import os
import time
from fabric.api import run, execute, hosts, cd
from bible.game import GameServer

class FTP(object):
    """
    Note:

    An example: pandora --ftp -r 30 -t 1200 -z -m 42.62.119.164 /tjmob_log/tjmob_37wan_1 /app/tjmob_37wan_1/backend/logs/game/dayreport/dayreport_2015-05-03.log.bz2*
    """
    def __init__(self, ip='42.62.119.164'):
        self.ip = ip

    def upload_log(self, gameserver, logtype=None, date=None, logfile=None):
        from bible.utils import BZIP2
        gameserver = GameServer(gameserver)
        ftp_log_path = '/{}_log/{}'.format(gameserver.game, gameserver.name)

        logtypes = ['dayreport', 'rtreport']

        date = date if date else time.strftime('%Y-%m-%d')

        if logfile:
            logfiles = [logfile]
        else:
            if logtype:
                logfiles = ['/app/{0}/backend/logs/game/{1}/{1}_{2}.log'.format(gameserver.name, logtype, date)]
            else:
                logfiles = ['/app/{0}/backend/logs/game/{1}/{1}_{2}.log'.format(gameserver.name, each_logtype, date) for each_logtype in logtypes]

        @hosts(gameserver.int_ip)
        def _upload_log():
            for each_log in logfiles:
                dir, filename = os.path.split(each_log)
                with cd(dir):
                    file_bz2 = '{}.bz2'.format(filename)
                    file_md5 = '{}.MD5'.format(file_bz2)
                    run('[ -f {0} ] && echo "{0} already exists" || {1} {2}'.format(file_bz2, BZIP2, filename))
                    run('[ -f {0} ] && echo "{0} already exists" || md5sum {1} >{0}'.format(file_md5, file_bz2))

                run('''pandora --ftp -r 30 -t 1200 -z -m {} {} {}.bz2*'''.format(self.ip, ftp_log_path, each_log) )

        execute(_upload_log)

