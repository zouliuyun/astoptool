一、添加服务器
天将雄师越狱服务器添加
http://mobile.gc.aoshitang.com/remote!server.action?action=add&isAppstore=false&gameId=tjxs&template=tjmob_37_&serverId=99999999&ip=120.132.69.53&host=s19.tjmob.aoshitang.com&port=8210
天将雄师appstore服务器添加
http://mobile.gc.aoshitang.com/remote!server.action?action=add&isAppstore=true&gameId=tjxs&template=tjmob_app_&serverId=999999&ip=120.132.69.151&host=s16.tjapp.aoshitang.com&port=8210

各个参数说明：
action          操作行为，add表示添加
isAppstore
是否appstore服，还是越狱服，true表示是appstore服务器，false为越狱混服
gameId=tjxs     固定值，游戏编号
template
表示要添加的运营管理后台的服务器ID编号前缀，目前有tjmob_37_表示越狱服，tjmon_app_表示appstore服
serverId        服务器编号，纯数字例如28
ip              开服IP
host            服务器域名，不带http,例如s16.tjapp.aoshitang.com
port            服务器端口号，例如8210

返回结果：
返回结果为json，其中success字段返回为true是表示成功，false表示失败，失败描述见msg
{"root":null,"msg":"success","success":true}
{"root":null,"msg":"相同的服务器ID已经存在！","success":false}

二、服务器维护

1、根据域名host查询所有和服的服务器ID
http://mobile.gc.aoshitang.com/remote!mixservers.action?serverUrl=s3.tjmob.aoshitang.com

参数说明：
serverUrl       游戏服务器的域名，是添加服务器时的host

返回结果
格式为json，success字段返回为true是表示成功，false表示失败，失败描述见msg
{"root":[{"gameId":"tjxs","serverId":"tjmob_37_9999"},{"gameId":"tjxs","serverId":"tjmob_37_99998"}],"msg":"success","success":true}
gameId          游戏标识
serverId        服务器的serverID

2、更新使即将和服的服务器处于维护状态【会自动生成txt】
http://mobile.gc.aoshitang.com/remote!maintain.action?action=close&gameId=tjxs&serverIds=tjmob_37_9999,tjmob_app_99998

参数说明：
action
表示本次执行的动作，close是关闭，服务器使其处于系统维护状态,open是开启处于流畅状态
gameId          固定值，游戏编号
serverIds
根据mixservers.action查询到的所有要和服的服务器ID：serverId字段，服务器Id以英文,分割

返回结果
格式为json，success字段返回为true是表示成功，false表示失败，失败描述见msg
{"root":null,"msg":"success","success":true}

3、更改需要和服服务器的信息
http://mobile.gc.aoshitang.com/remote!server.action?action=update&gameId=tjxs&ip=ssss&host=ssss&port=sss&time=2015-08-07
10:00:00&serverIds=tjmob_37_2,tjmob_37_9999,tjmob_app_2,tjmob_app_99998

参数说明：
action          操作行为update表示更新
gameId          固定值，游戏编号
ip              开服IP【可不传】
host            服务器域名，不带http,例如s16.tjapp.aoshitang.com【可不传】
port            服务器端口号，例如8210【可不传】
time            开服时间，时间格式为2015-03-23 15:10:00【可不传】
serverIds       服务器Id以英文,分割，例如tjmob_app_2,tjmob_app_99998


返回结果：
格式为json，success字段返回为true是表示成功，false表示失败，失败描述见msg
{"root":null,"msg":"success","success":true}

4、更新使合服完毕的服务器处于流畅状态【会自动生成txt】
http://mobile.gc.aoshitang.com/remote!maintain.action?action=open&gameId=tjxs&serverIds=tjmob_37_9999,tjmob_app_99998

参数说明：
action
表示本次执行的动作,open是开启处于流畅状态，close是关闭，服务器使其处于系统维护状态
gameId          固定值，游戏编号
serverIds
根据mixservers.action查询到的所有要和服的服务器ID：serverId字段，服务器Id以英文,分割

返回结果
格式为json，success字段返回为true是表示成功，false表示失败，失败描述见msg
{"root":null,"msg":"success","success":true}

#####################################################################################################
根据域名获取服务器列表需要已上线
http://mobile.gc.aoshitang.com/remote!mixservers.action?serverUrl=s16.tjmob.aoshitang.com

返回结果格式如下：
appStore:布尔值，表示是否是appStore的serverID
gameId：String，游戏Id
serverId：String，服务器Id
{"root":[{"appStore":false,"gameId":"tjxs","serverId":"tjmob_37_16"},{"appStore":false,"gameId":"tjxs","serverId":"tjmob_37_17"},{"appStore":false,"gameId":"tjxs","serverId":"tjmob_37_18"}],"msg":"success","success":true}
 
#####################################################################################################
mobile_entrance_list是手游用来跟官网组的服务器入口控制对接的接口模板
例如攻城手游系列入口控制地址:http://mobile.gc.aoshitang.com

格式如下:
game@language@yx@isAppstore@gameId@templateID@target_url

举例:
tjmob@cn@37wan@false@tjxs@tjmob_37_@mobile.gc.ruizhan.com


#####################################################################################################
详细接口参数举例如下:

天将雄师越狱服务器添加
http://mobile.gc.ruizhan.com/remote!server.action?action=add&isAppstore=false&gameId=tjxs&template=tjmob_37_&serverId=29&time=2015-10-10 10:10:00&ip=120.132.69.53&host=s19.tjmob.ruizhan.com&port=8210
天将雄师越狱服务器修改
http://mobile.gc.ruizhan.com/remote!server.action?action=update&isAppstore=false&gameId=tjxs&template=tjmob_37_&serverId=29&time=2015-03-23 18:10:00&ip=120.132.69.53&host=s29.tjmob.ruizhan.com&port=8210

天将雄师appstore服务器添加
http://mobile.gc.ruizhan.com/remote!server.action?action=add&isAppstore=true&gameId=tjxs&template=tjmob_app_&serverId=16&time=2015-10-10 10:10:00&ip=120.132.69.151&host=s16.tjapp.ruizhan.com&port=8210
天将雄师appstore服务器修改
http://mobile.gc.ruizhan.com/remote!server.action?action=update&isAppstore=true&gameId=tjxs&template=tjmob_app_&serverId=16&time=2015-03-23 15:10:00&ip=120.132.69.151&host=s16.tjapp.ruizhan.com&port=8210


各个参数说明：
action          操作行为，add表示添加，update表示更新
isAppstore      是否appstore服，还是越狱服，true表示是appstore服务器，false为越狱混服
gameId=tjxs     固定值，游戏编号
template        表示要添加的运营管理后台的服务器ID编号前缀，目前有tjmob_37_表示越狱服，tjmob_app_表示appstore服
serverId        服务器编号，纯数字例如28
time            开服时间，时间格式为2015-03-23 15:10:00
ip              开服IP
hosts           服务器域名，不带http,例如s16.tjapp.ruizhan.com
port            服务器端口号，例如8210



#####################################################################################################

【表1-攻城添加】
攻城掠地越狱服务器关闭维护
http://mobile.gc.aoshitang.com/remote!maintain.action?action=close&isAppstore=false&gameId=gcld&template=feiliu&serverIds=9999,10000
攻城掠地越狱服务器开启
http://mobile.gc.aoshitang.com/remote!maintain.action?action=open&isAppstore=false&gameId=gcld&template=feiliu&serverIds=9999,10000

【表2-攻城添加】
攻城掠地appstore服务器[feiliuapp]关闭维护
http://mobile.gc.aoshitang.com/remote!maintain.action?action=close&isAppstore=true&gameId=gcld&template=feiliuapp&serverIds=9999,10000
攻城掠地appstore服务器[feiliuapp]开启
http://mobile.gc.aoshitang.com/remote!maintain.action?action=open&isAppstore=true&gameId=gcld&template=feiliuapp&serverIds=9999,10000

各个参数说明：
action
操作行为，close表示关闭，open表示更新，调用完后自动生成维护或者开启的txt文件
isAppstore
是否appstore服，还是越狱服，true表示是appstore服务器，false为越狱混服
gameId=gcld     固定值，游戏编号
template
表示要添加的运营管理后台的服务器ID编号前缀，目前有【表1】模板template表示越狱服，【表2】feiliuapp表示appstore服【注意，这里要维护的服模板都要调用】
serverIds       服务器编号，纯数字，以英文,分割

