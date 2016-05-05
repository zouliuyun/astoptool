# -*- coding:utf-8 -*-

from ConfigParser import ConfigParser

class ConfigReader(object):
    """
    为傲世堂的游戏项目配置文件定制的配置读取类。
    陈超写的arg.gameOption耦合性太强，只能在bible内使用。
    但是配置文件的结构设计的很合理。

    此类就是根据原来的结构设计重新写的解耦并且适用性更广的类。

    Example::

        conf = ConfigReader(game, region)
        ip = conf.get("mobile_www_ip")
        if conf.has_option("mobile_www_port")
            port = conf.getint("mobile_www_port")     
    """
    def __init__(self, game, section, conf_dir='/app/opbin/work/bible/conf'):
        self.game = game
        self.section = section
        self.conf_file = '{}/{}.conf'.format(conf_dir.rstrip('/'), self.game)
        self.config = ConfigParser()
        self.config.read(self.conf_file)
        self.has_section = self.config.has_section(self.section)

    def has_option(self, option):
        return self._has_option(self.section, option) or self._has_option('common', option)

    def _has_option(self, section, option):
        return self.config.has_option(section, option)

    def get(self, option, raw=0, var=None):
        if self._has_option(self.section, option):
            return self.config.get(self.section, option, raw, var)
        elif self._has_option('common', option):
            return self.config.get('common', option, raw, var)
        else:
            raise Exception("Can't find option: {} in {}".format(option, self.conf_file))

    def getint(self, option):
        if self._has_option(self.section, option):
            return self.config.getint(self.section, option)
        elif self._has_option('common', option):
            return self.config.getint('common', option)
        else:
            raise Exception("Can't find option: {} in {}".format(option, self.conf_file))

    def getfloat(self, option):
        if self._has_option(self.section, option):
            return self.config.getfloat(self.section, option)
        elif self._has_option('common', option):
            return self.config.getfloat('common', option)
        else:
            raise Exception("Can't find option: {} in {}".format(option, self.conf_file))

    def getboolean(self, option):
        if self._has_option(self.section, option):
            return self.config.getboolean(self.section, option)
        elif self._has_option('common', option):
            return self.config.getboolean('common', option)
        else:
            raise Exception("Can't find option: {} in {}".format(option, self.conf_file))


