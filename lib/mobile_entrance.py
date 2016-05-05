#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用来添加或者更新运营控制的官网入口中游戏服的详细信息，避免运营填错，请使用-h查看参数说明文档。

Request url example:
http://mobile.gc.ruizhan.com/remote!server.action?action=update&isAppstore=false&gameId=tjxs&template=tjmob_37_&serverId=29&time=2015-03-23 18:10:00&ip=120.132.69.53&host=s29.tjmob.ruizhan.com&port=8210

Template example:
tjmob@appstore@appstore@true@tjxs@tjmob_app_@mobile.gc.ruizhan.com

2015-03-30 Xiaoyu Created
"""

import requests
from fabric.api import local, quiet

from bible.config_reader import ConfigReader

MOBILE_ENTRANCE_LIST = '/app/opbin/work/bible/mobile_entrance_list'


def _local_resolver(domain):
    with quiet():
        ret_value = local('''nslookup %s |grep "^Address" |grep -v '#'|awk '{print $2}' ''' % domain, capture=True)
    if ret_value:
        return ret_value
    else:
        raise Exception('Fail to resolve {} to ip address'.format(domain))
    

class MobileEntrance(object):
    """
    开服入口和开服列表控制的类，支持添加，更新，开启，关闭功能。
    TODO: 添加合服接口
    """
    def __init__(self, game, language, yx, id):
        self.game = game
        self.language = language
        self.region = self.language
        self.yx = yx
        self.id = id
        self.request_url = None
        self.mode = self.mobile_entrance_mode()
    
    def mobile_entrance_mode(self):
        conf = ConfigReader(self.game, self.region)
        if conf.has_option('mobile_entrance_mode'):
            return conf.getint('mobile_entrance_mode')
        else:
            return 1

    def _send_requests(self, remote_action, data, entrance_url):
        _ip = _local_resolver(entrance_url)
        headers = {'host': entrance_url}
        r = requests.get("http://{}/remote!{}.action".format(_ip, remote_action), params=data, headers=headers)
        self.request_url = r.url
        #print(self.request_url)
        return r.json()

    def _get_hold_of_template(self):
        ret_value = []

        try:
            with open('{}/{}'.format(MOBILE_ENTRANCE_LIST, self.game), 'r') as f:
                lines = f.readlines()
        except:
            self.has_template = None
            print('[警告] 未在 {}/{} 里找到项目模板,请添加项目模板或手动控制入口信息。'.format(MOBILE_ENTRANCE_LIST, self.game))
            return ret_value

        for each_line in lines:
            if each_line.startswith('{}@{}@{}@'.format(self.game, self.language, self.yx)):
                game, language, yx, isAppstore, gameId, template, entrance_url = each_line.split('@')
                entrance_url = entrance_url.strip('\n ')
                data = {'isAppstore': isAppstore,
                        'gameId': gameId,
                        'template': template}
                ret_value.append((data, entrance_url))

        if ret_value:
            self.has_template = True
        else:
            self.has_template = None
            print('[警告] 未在 {}/{} 里找到可使用的模板,请添加模板或手动控制开服入口信息。'.format(MOBILE_ENTRANCE_LIST, self.game))

        return ret_value

    def _op(self, type, _data):
        data = self._get_hold_of_template()
        if data:
            ret = [] 
            for each_tuple in data:
                entrance_url = each_tuple[1]
                _data.update(each_tuple[0])
                result_json = self._send_requests(type, _data, entrance_url)
                if result_json['msg'] == 'success':
                    result = True
                else:
                    result = False
                ret.append(result)

            if all(ret):
                return True
            else:
                return False
        else:
            return None

    def query(self, dns):
        if self.mode == 2:
            dns = 'http://{}/root/'.format(dns)

        _data = {'serverUrl': dns}
        entrance_urls  = [each[1] for each in self._get_hold_of_template()]
        uniq_entrance_url = list(set(entrance_urls)) #expect only one entrance_url
        if len(uniq_entrance_url) != 1:
            raise Exception('One and only one entrance_url should be found in the template for game: {}, region: {}'.format(self.game, self.region))
        self.entrance_url = uniq_entrance_url[0]

        return self._send_requests('mixservers', _data, self.entrance_url)

    def merge(self, old_dns, new_dns, new_ip, new_port):
        result_json = self.query(old_dns)
        print(result_json)
        items = result_json['root']
        print(items)
        game_id = items[0]['gameId'] #only one game_id is expected.
        server_ids = [each['serverId'] for each in items]

        data = {'action': 'update',
                'gameId': game_id,
                'ip': new_ip,
                'host': new_dns,
                'port': new_port,
                'serverIds': ','.join(server_ids)}

        result = self._send_requests('server', data, self.entrance_url)

        if result['success']:
            return True
        else:
            return False

#        for each_item in items:
#            print('Change for {}'.format(each_item))
#            game_id = each_item['gameId']
#            _game, _yx, _id = each_item['serverId'].split('_')
#            template = '{}_{}_'.format(_game, _yx)
#            server_id = _id
#            is_appstore = each_item['appStore']
#            data = {'action': 'update',
#                    'isAppstore': is_appstore,
#                    'gameId': game_id,
#                    'template': template,
#                    'serverId': server_id,
#                    'ip': new_ip,
#                    'host': new_dns,
#                    'port': new_port}
#
#            result = self._send_requests('server', data, self.entrance_url)
#            print(result)

    def add(self, dns, ip, port):

        if self.mode == 2:
            dns = 'http://{}/root/'.format(dns)

        _data = {'action': 'add',
            'serverId': self.id,
            'ip': ip,
            'host': dns,
            'port': port}
        return self._op('server', _data)
            
    def update(self, dns, ip, port):
        if self.mode == 2:
            dns = 'http://{}/root/'.format(dns)

        _data = {'action': 'update',
            'serverId': self.id,
            'ip': ip,
            'host': dns,
            'port': port}
        return self._op('server', _data)

    def open(self):
        _data = {'action': 'open',
            'serverId': self.id}

        return self._op('maintain', _data)

    def maintain(self):
        _data = {'action': 'close',
            'serverId': self.id}

        return self._op('maintain', _data)

