#!/usr/bin/env python
#-*- coding:utf8 -*-

import common
import json

from fabric.api import run, execute, hosts, local
from bible.arg import gameOption


########################################################################
#陈超写的
def executeBackstage(url,data,header,msg):
    status,stdout = common.urlopen(url,header=header,data=data)
    result = {"status":False}
    result["response"] = stdout
    if status == 0:
        try:
            jsonResult = json.loads(stdout)
            statusCode = int(jsonResult["status"])
            if statusCode == 1:
                result["status"] = True
                result["msg"] = msg
            else:
                result["status"] = False
                result["msg"] = jsonResult["msg"]
        except Exception,e1:
            result["status"] = False
            result["msg"] = stdout
    else    :
        result["status"] = False
        result["msg"] = stdout
    return result
def addBackstage(backstage_interface_url,data,header):
    url = "http://%s/backStage!addServer.action"%backstage_interface_url
    return executeBackstage(url,data,header,"添加后台成功")
def mixBackstage(backstage_interface_url,data,header):
    url = "http://%s/backStage!mixServer.action"%backstage_interface_url
    return executeBackstage(url,data,header,"设置混服成功")
def upBackstage(backstage_interface_url,data,header):
    url = "http://%s/backStage!editeServer.action"%backstage_interface_url
    return executeBackstage(url,data,header,"修改后台成功")
def addPartner(backstage_interface_url,data,header):
    url = "http://%s/backStage!addPartner.action"%backstage_interface_url
    return executeBackstage(url,data,header,"添加新联运成功")
#End 陈超写的 
########################################################################

class Backstage(object):
    """
    Author: Xiaoyu

    .. merge:
    curl -H "host:bs.gc.aoshitang.com" --retry 3 --retry-delay 5 --data "mix=1073_S210&master=1073_S208" http://10.6.197.229/backStage\!mixServer.action
    {"count":"0","status":"1","msg":"success"}
    """
    def __init__(self, game, region='cn', backstage_interface_url=None, backstage_header=None, int_ip=None):
        self.game = game
        self.region = region
        self._debug = False

        #if not self._debug:
        #    from fabric.api import output
        #    output.everything = False

        from bible import state
        state.language = self.region
        state.game = self.game
        
        self.int_ip = int_ip
        self.backstage_header = backstage_header
        self.backstage_interface_url = backstage_interface_url

        if not self.int_ip:
            self.int_ip = gameOption('backstage')
            if not self.int_ip:
                raise Exception("Can't get value for backstage ip in bible config file")

        if not self.backstage_header:
            self.backstage_header = gameOption('backstage_header')
            if not self.backstage_header:
                raise Exception("Can't get value for backstage_header in bible config file")

        if not self.backstage_interface_url:
            self.backstage_interface_url = gameOption('backstage_interface_url')
            if not self.backstage_interface_url:
                raise Exception("Can't get value for backstage_interface_url in bible config file")

    def merge(self, s_server, t_server):
        """
        合服
        .. 被合服: s_server
        .. 保留服: t_server
        """
        import json
        
        game, t_yx, t_id = t_server.split('_')
        game, s_yx, s_id = s_server.split('_')

        cmd = '''curl -H "host:{}" --retry 3 --retry-delay 5 --data "mix={}_S{}&master={}_S{}" http://{}/backStage\\!mixServer.action'''.format(self.backstage_header, s_yx, s_id, t_yx, t_id, self.backstage_interface_url)
        result = local(cmd, capture=True)
        json_result = json.loads(result)
        status = json_result['status']
        if status == '1':
            return True
        else:
            print('The error msg for "{}" is {}'.format(cmd, json_result['msg']))
            return False


if __name__ == "__main__":
    #data = {}
    #data["servername"] = "37wan_S1"
    #data["start_time"] = "2014-10-10 09:00:00"
    #print upBackstage("10.6.196.49",data,"bs.tjmob.aoshitang.com")
    import state
    state.game = "zjzr"
    state.language = "cn_xianyu"
    backstage_interface_url = "10.6.196.43" 
    #data = {'w_ip': '122.225.219.35', 'servername': 'feiliu_S88889', 'cnc_ip': '122.225.219.35', 'n_ip': '10.6.196.30'} 
    data = {'mix': 'baidu91_S1', 'master': 'xianyu_S1'}
    header = "bs.zjzr.aoshitang.com"
    print mixBackstage(backstage_interface_url,data,header)
