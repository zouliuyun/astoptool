# -*- coding: utf-8 -*-
"""
生产环境新的大混服联运添加和删除。

.. 添加
    添加操作将会，拷贝FTP上的new_yx.properties到/app/opbin/work/${game}/allinone/newserver/${region}/properties/目录下，然后再传输到运维资源下载服务器供布服时下载。

.. 删除
    TODO 考虑到暂时不会有联运停止合作的需求，此功能暂不考虑。 
        
"""

class GameProject(object):
    """
    GameProject 类，目前可以使用的是:
    1、获取所有游戏服信息;
    2、转换游戏服跟ip的对应关系，以使Fabric提高效率;

    后续功能添加中...
    """
    def __init__(self, game, region='cn'):
        self.game = game

    @property
    def servers(self):
        """
        Get all game server info. It will get a dict like:
        
        { 'astd_17wan_1': '10.6.120.23', 
          'astd_37wan_98': '10.4.5.5',
                     .
                     .
                     .
          'astd_37wan_8': '10.4.5.15'}
   
        """
        server_info = getserverlist()
        _server_info_dict = {'{}_{}'.format(self.game, each[0]): each[1] for each in server_info}
        return _server_info_dict
 
    def transform(self, game_servers, all_info=None):
        """
        Transform funcion. 
        eg: it will transformat from 
            ['astd_37wan_2', 'astd_51wan_99', 'astd_uoyoo_90']
        to
            {
                '10.6.20.1':['astd_37wan_2', 'astd_51wan_99'], 
                '10.6.20.2':['astd_uoyoo_90']
            }
        """
        if not all_info:
            all_info = self.servers

        ips = list(set([all_info[each] for each in game_servers]))
        locate_game_servers = {each:[] for each in ips}
        for each in game_servers:
            locate_game_servers[all_game_server_info[each]].append(each)
        return locate_game_servers
 
