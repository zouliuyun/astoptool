#!/usr/bin/env python
#-*- coding:utf8 -*-
'''
连接状态文件，所有连接使用这个状态文件
'''
import threading

#gw建立连接的锁
gw_lock = threading.Lock()
#ip connect 锁
ip_lock = threading.Lock()
#建立连接池
have_connectCache = []
#ssh 并发数目
sshThreadingCount = 40
#并发数目
threadingCount = 40
#并发间隔数,及每一轮并发后是否需要等待几秒再执行下一轮并发，不等待则为None，单位为秒
threadInterval = None
#ssh连接尝试次数
sshtry = 10
#ssh timeout
sshTimeOut = 5
#ssh port
port = 22
#ssh user
user = "astd"
#游戏服跟ip对应[["feiliu_1","1.1.1.1"],....]
servers = []
#建立的ssh连接,key为ip，value为ssh的transport
connectionCaches = {}
#命令执行结果字典
result = {}
#连接错误的ip列表
errorHost = []
#是否忽略错误主机
ignoreErrorHost = False
#执行错误的信息
errorResult = {}
#ssh是否已经开始初始化,每次初始化时修改该值,请不要设置该值为True！！！！！！！！！！！！
sshInit = False
#操作的项目
game = None
#操作项目的语种
language = None
#操作类型
action = None
#游戏配置conf配置文件
gameconf = None
#main conf配置文件
mainconf = None
#执行该脚本输入的参数options
options = None
