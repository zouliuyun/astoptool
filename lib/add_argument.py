#~*~coding:utf8~*~

def add_main(parser):
    parser.add_argument(
        "-g", 
        "--game", 
        dest="game", 
        required=True, 
        help="项目代号，比如:gcmob"
    )
    parser.add_argument(
        "-l", 
        "--region", 
        dest="language", 
        required=True, 
        help="国家/地区，比如:cn, vn, ft"
    )

def add_serverlist(parser):
    parser.add_argument(
        "--startdate", 
        dest="startdate", 
        help="游戏列表开服开始时间"
    )
    parser.add_argument(
        "--enddate", 
        dest="enddate", 
        help="游戏列表开服结束时间"
    )
    parser.add_argument(
        "-s", 
        "--serverlist", 
        dest="serverlist", 
        help="游戏服列表，游戏精确匹配"
    )
    parser.add_argument(
        "-e", 
        "--excludeServerlist", 
        dest="excludeServerlist", 
        help="游戏服排除列表，正则精确匹配"
    )
    parser.add_argument(
        "-u", 
        "--uniqserver", 
        dest="uniqserver", 
        action="store_true", 
        help="去重服务器ip"
    )
    parser.add_argument(
        "-f", 
        "--serverfile", 
        dest="serverfile", 
        default=None, 
        help="服务器列表文件(列表文件为绝对路径)"
    )

