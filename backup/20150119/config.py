#!/usr/bin/env python
#~*~coding:utf8~*~
import ConfigParser
import os

def getConfig(game):
    config = ConfigParser.ConfigParser()
    dir = os.path.dirname(os.path.abspath(__file__))
    path = "%s/../conf/" %dir
    filepath = path + game + ".conf"
    if not os.path.exists(filepath):
        raise("ERROR: %s该配置文件不存在！"%game)
    config.read(filepath)
    return config
if __name__ == "__main__":
    getConfig("gcmob")
