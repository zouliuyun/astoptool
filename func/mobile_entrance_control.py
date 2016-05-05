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
from bible.mobile_entrance import MobileEntrance

 
def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Add or update Mobile Entrance control infomation.'
    )

    parser.add_argument(
        '-t',
        type=str,
        nargs=1,
        metavar='GameServer',
        dest='gameServer',
        help='game server, eg: game_37wan_58'
    )
    parser.add_argument(
        '-l',
        type=str,
        nargs=1,
        dest='language',
        help='language, eg: cn or appstore'
    )
    parser.add_argument(
        '-d',
        type=str,
        nargs=1,
        dest='dns',
        help='dns'
    )
    parser.add_argument(
        '-o',
        type=str,
        nargs=1,
        choices=['add', 'update'],
        dest='op',
        help='add or update? eg: add'
    )    
    parser.add_argument(
        '-i',
        type=str,
        nargs=1,
        dest='ip',
        help='external IP address'
    )
    parser.add_argument(
        '-p',
        type=str,
        nargs=1,
        dest='port',
        help='port, eg: 8210'
    )
#    parser.add_argument(
#        '-T',
#        type=str,
#        nargs=1,
#        metavar='TIME',
#        dest='startTime',
#        help='start time for the game server, eg: "2015-09-09 10:00:00"'
#    )

    args = parser.parse_args()

    if args.gameServer and args.dns and args.op and args.ip and args.port and args.language:
        gameServer = args.gameServer[0].strip()
        dns = args.dns[0].strip()
        op = args.op[0].strip()
        ip = args.ip[0].strip()
        port = args.port[0].strip()
        lan = args.language[0].strip()
        
        game, yx, id = gameServer.split('_')
    
        mobile_entrance = MobileEntrance(game, lan, yx, id)
        op_method = getattr(mobile_entrance, op)
        ret_value = op_method(dns, ip, port)
        if ret_value:
            print('[SUCC] Mobile Entrance added successfully')
        else:
            if mobile_entrance.request_url:
                print('''[FAIL] Please try again.. " curl '{}' " '''.format(mobile_entrance.request_url))

    else:
        parser.print_help()

    
if __name__ == '__main__':
    main()
