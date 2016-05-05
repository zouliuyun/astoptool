#-*- coding:utf8 -*-

from fabric.api import run, quiet, local, execute, env
import time

from bible.utils import TIMESTAMP

RELEASE_TYPE = 'temp_task'
REMOTE_DIR = '/app/opbak/{}_{}'.format(RELEASE_TYPE, TIMESTAMP)

#########################################
#class Config
def _shell_sed_escape(string):
    string = string.replace('\\', '\\\\\\\\')
    for char in ('/', '!', '$', '@', '"', "'"):
        string = string.replace(char, '\%s' % char)
    return string


class Config(object):
    """
    很基础的Config类，依赖于Fabric, 支持add, modify, delete操作。
    仅支持游戏服的配置修改。

    创建实例的话，需要在cd后使用，如：
    with cd('/path/to/file'):
        config1 = Config('the_file')
        config1.modify(key='the_key', value='some_value')

    """
    def __init__(self, filename, remote_dir=REMOTE_DIR):
        self.filename = filename

        with quiet():
            has_the_file = run('test -f {}'.format(filename)).succeeded

        if not has_the_file:
            raise Exception('File {} NOT exists under backend/apps/'.format(filename))
        
        self.dir = run('pwd')
        gameServer = self.dir.split('/')[2]
        backup_dir = '{}/{}'.format(remote_dir, gameServer)
        run('[ -d {0} ] || mkdir -p {0}'.format(backup_dir))
        run('cp {} {}/'.format(self.filename, backup_dir))

    def has_the_key(self, key):
        with quiet():
            _has_the_key = run('grep --color=never "^{} *=" {}'.format(key, self.filename)).succeeded
        return _has_the_key
        
    def add(self, key, value, comment='null'):
        """
        添加配置项和注释
        """
        if self.has_the_key(key):
            print('[Warning] the key: {} already exists in {}/{}. Nothing changed.'.format(key, self.dir, self.filename))

        else:
            if comment.lower() == 'null':
                raise Exception("The comment can't be null if you want to add a new key.")

            _comment = "#{}".format(comment.lstrip('# '))
            key_value_combine = _shell_sed_escape("{} = {}".format(key, value))
            run('''sed -i '$a {}' {}'''.format(_comment, self.filename))
            run('''sed -i '$a {}' {}'''.format(key_value_combine, self.filename))

    def modify(self, key, value, comment=None):
        """
        修改配置项
        """
        if self.has_the_key(key):
            _value = _shell_sed_escape(value)
            run('''sed -i '/^{0} *=/c {0} = {1}' {2}'''.format(key, _value, self.filename), shell_escape=False)
        else:
            raise Exception('The key: {} NOT exists in {}/{}'.format(key, self.dir, self.filename))
    
    def delete(self, key, value=None, comment=None):
        """
        删除配置项
        """
        if self.has_the_key(key):
            result = run('grep --color=never -n -B1 "^{} *=" {}'.format(key, self.filename))
            lines = result.splitlines()
            if len(lines) == 2:
                #如果存在注释行的话，删除注释行
                rowNum, comment = lines[0].split('-', 1) #获取注释行的行号
                if comment.startswith('#'):
                    run("sed -i '{}d' {}".format(rowNum, self.filename))

            run('''sed -i '/^{} *=/d' {}'''.format(key, self.filename))
        else:
            print('[Warning] the key: {} does NOT exist in {}/{}. Nothing changed.'.format(key, self.dir, self.filename))

#End class Config
#####################################################

