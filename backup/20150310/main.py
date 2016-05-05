#!/usr/local/bin/python
#~*~coding:utf8~*~
import sys, os, json
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)) + "/lib")
import argparse
import ConfigParser

from func import allGameExecSql,gameSqlExecute

import check, state, serverlist
from arg import *

from func.testEnvRelease import add_args_for_testEnvRelease
from func.testEnvPayProxyRelease import add_args_for_testEnvPayProxyRelease
from func.testEnvModifyConfig import add_args_for_testEnvModifyConfig

def printServerlist():
    for i in getserverlist():
        #print i
        if isinstance(i, list):
            print i[0] + "@" + i[1]
        else:
            print i 
    #print json.dumps(getserverlist())
def add_main(parser):
    parser.add_argument("-g", "--game", dest="game", required=True, help="指定项目名称，比如:gcmob")
    parser.add_argument("-l", "--language", dest="language", required=True, help="指定语言，比如:cn, vn, ft")
def add_serverlist(parser):
    parser.add_argument("--startdate", dest="startdate", help="游戏列表开服开始时间")
    parser.add_argument("--enddate", dest="enddate", help="游戏列表开服结束时间")
    parser.add_argument("-s", "--serverlist", dest="serverlist", help="游戏服列表，游戏精确匹配")
    parser.add_argument("-e", "--excludeServerlist", dest="excludeServerlist", help="游戏服排除列表，正则精确匹配")
    parser.add_argument("-u", "--uniqserver", dest="uniqserver", action="store_true", help="去重服务器ip")
    parser.add_argument("-f", "--serverfile", dest="serverfile", default=None, help="服务器列表文件")
def deploy_fun(options):
    from func import deploy
    newserver = deploy.deploy(game, language, options.servername, options.ip, options.cleartime, title=options.title, gameurl=options.gameurl, asturl=options.asturl, skipcheck=options.skipcheck)
    newserver.run()
def cmd_func(options):
    from func import cmd
    cmd.cmd(options.cmd)
def put_func(options):
    from func import put
    put.put(options.localfile, options.remotefile)
def recover_func(options):
    from func import recover3
    recoverserver = recover3.recover(game, language, options.servername, options.ip, options.recoverType)
    recoverserver.run()
def kfgz_func(options):
    from func import kfgz
    kfgz = kfgz.kfgz(game, language, options.level, options.days, options.enddate, options.hfdate)
    kfgz.run()
def moveserver_func(options):
    from func import recoverByProject
    recoverByProject.recoverByProject(options.failureip, options.recoverip)
def recoverbinlog_func(options):
    from func import recoverByMysql
    recoverByMysql.recoverByMysql(options.failureip, options.recoverDate, options.serverfile)
def deploymix_func(options):
    from func import deployMix
    newserver = deployMix.deploy(game, language, options.servername, options.mainserver, options.restart, title=options.title, gameurl=options.gameurl, asturl=options.asturl, skipcheck=options.skipcheck)
    newserver.run()
def resetcleartime_func(options):
    from func import resetClearTime
    resetClearTime.reset(options.cleartime, options.starttime, options.servername)
def addwhiteip_func(options):
    from func import addwhiteip
    addwhiteip.addwhiteip(options.iplist, options.yx)
def template_func(options):
    from func import template
    newserverTemplate = template.template(game, language, options.servername, options.ip, options.port , options.mainServername)
    if options.templatetype:
        type = options.templatetype.split(",")
        for i in type:
            if i.strip() == "":
                continue
            check = False
            if i.strip() in ["sql", "all"]:
                newserverTemplate.updateServerSql()
                check = True
            if i.strip() in ["common", "all"]:
                newserverTemplate.updateServerLib()
                check = True
            if i.strip() in ["gametemplate", "all"]:
                newserverTemplate.updateServerConf()
                check = True
            if i.strip() in ["properties", "all"]:
                newserverTemplate.updateServerProperties()
                check = True
            if i.strip() in ["www", "all"]:
                newserverTemplate.updateServerWww()
                check = True
            if i.strip() in ["nginx", "all"]:
                newserverTemplate.updateServerNginxConf()
                check = True
            if not check:
                print "不支持的模板类型:" + i
                sys.exit(1)
    else:
        print "请输入生成模板的类型"
def alltemplate_func(options):
    from func import alltemplate
    alltemplate.alltemplate(options.templatetype)
def serverlist_func(options):
    printServerlist()
def mobileWwwTestUpdate_func(options):
    from func import mobile_www_test_update
    mobile_www_test_update.init(game, language, options.version, options.updateType, options.hd)
def mobileWwwUpdate_func(options):
    from func import mobile_www_update
    mobile_www_update.update(game, language, options.version, options.updateType, options.hd)
def update_func(options):
    from func import update
    #update.update(options.sqlOrNot, options.sqlFile, options.backendUpload, options.backendChangeOrNot, options.backendName, options.executeVersionList, options.restart, options.resourceDir, options.replaceFile, options.addFile, options.addContent, options.specialScript, options.executeFirst, frontName)
    update.update(options.sqlFile, options.backendName, options.executeVersionList, options.executeDbVersionList, options.restart, options.resourceDir, options.replaceFile, options.addFile, options.addContent, options.specialScript, options.executeFirst, options.frontName)
def hotswap_func(options):
    from func import hotswap
    hotswap.hotswap(options.hotswapType, options.keyword, options.backend)   
def restart_func(options):
    from func import restart
    restart.restart(options.restartType)
def assetrooms_func(options):
    from func import assets_count
    assets_count.assetrooms(options.gamerooms, options.projecttag)
def mobileWwwTestEnvAdd_func(options):
    from func import mobileWwwTestEnvironmentAdd
    mobileWwwTestEnvironmentAdd.mobileWwwTestEnvironmentAdd(options.ip)
def mobileWwwTestEnvDel_func(options):
    from func import mobileWwwTestEnvironmentDel
    mobileWwwTestEnvironmentDel.mobileWwwTestEnvironmentDel(options.ip)
def testEnvRelease_func(options):
    from func import testEnvRelease
    release = testEnvRelease.Release(options)
    release.run()
def testEnvPayProxyRelease_func(options):
    from func import testEnvPayProxyRelease
    release = testEnvPayProxyRelease.Release(options)
    release.run()
def testEnvModifyConfig_func(options):
    from func import testEnvModifyConfig
    release = testEnvModifyConfig.Release(options)
    release.run()

def arg_init():
    global options
    global config
    config = ConfigParser.ConfigParser()
    dir = os.path.dirname(os.path.abspath(__file__))
    conf = dir + "/conf"
    #切换目录到文件所在目录
    parser = argparse.ArgumentParser(prog="bible", description="统一运维工具提供常用功能，包含布服、修改开服时间、模板创建、更新等等功能") 

    subparser = parser.add_subparsers(title="统一运维工具", description="可用功能", help="功能具体使用", dest="action")

    #游戏服部署
    deploy_parser = subparser.add_parser("deploy", help="游戏服部署")
    add_main(deploy_parser)
    deploy_parser.add_argument("-s", "--servername", dest="servername", required=True, help="指定游戏服名称，比如:feiliu_1")
    deploy_parser.add_argument("-C", "--cleartime", dest="cleartime", required=True, help="游戏清档时间")
    deploy_parser.add_argument("-i", "--ip", dest="ip", required=True, help="ip地址，比如:1.1.1.1")
    deploy_parser.add_argument("-t", "--title", dest="title", help="游戏www标题")
    deploy_parser.add_argument("-u", "--gameurl", dest="gameurl", help="游戏域名")
    deploy_parser.add_argument("-a", "--asturl", dest="asturl", help="游戏域名对应的ast的cname域名")
    deploy_parser.add_argument("--skipcheck", dest="skipcheck", action="store_true", help="布服前不进行游戏是否存在检查")
    deploy_parser.set_defaults(func=deploy_fun)
    
    #命令执行参数列表
    cmd_parser = subparser.add_parser("cmd", help="命令执行")
    add_main(cmd_parser)
    cmd_parser.add_argument("-c", "--cmd", dest="cmd", required=True, help="执行命令，${flag}表示游戏服比如:feiliu_1, ${game}表示项目名比如:gcmob")
    add_serverlist(cmd_parser)
    cmd_parser.set_defaults(func=cmd_func)
    
    #上传文件参数列表
    put_parser = subparser.add_parser("put", help="文件上传")
    add_main(put_parser)
    put_parser.add_argument("-F", "--localfile", nargs="+", dest="localfile", required=True, help="本地文件")
    put_parser.add_argument("-R", "--remotefile", dest="remotefile", required=True, help="远端文件路径")
    add_serverlist(put_parser)
    put_parser.set_defaults(func=put_func)

    #恢复游戏服的参数列表
    recover_parser = subparser.add_parser("recover", help="游戏恢复")
    add_main(recover_parser)
    recover_parser.add_argument("-s", "--servername", dest="servername", help="指定游戏服名称，比如:feiliu_1")
    recover_parser.add_argument("-i", "--ip", dest="ip", help="ip地址，比如:1.1.1.1")
    recover_parser.add_argument("-t", "--recoverType", dest="recoverType", choices=["recoverhadoop", "recoverbinlog"], help="恢复类型")
    recover_parser.set_defaults(func=recover_func)
    #恢复游戏服的参数列表
    kfgz_parser = subparser.add_parser("kfgz", help="跨服国战排赛")
    add_main(kfgz_parser)
    kfgz_parser.add_argument("-L", "--level", dest="level", help="指定活跃等级，比如：60")
    kfgz_parser.add_argument("-n", "--days", dest="days", help="定义n天内登陆的玩家为活跃玩家")
    kfgz_parser.add_argument("-d", "--enddate", dest="enddate", help="参赛范围，指定开服时间截止为该时间的游戏才能参赛，如2015-03-06 23:59:59")
    kfgz_parser.add_argument("-H", "--hfdate", dest="hfdate", help="上一次跨服国战时间或者上次跨服国战后第一次合服前的任意时间点")
    kfgz_parser.set_defaults(func=kfgz_func)
    
    #移动整机游戏服到另一台
    moveserver_parser = subparser.add_parser("moveserver", help="迁移整机")
    add_main(moveserver_parser)
    moveserver_parser.add_argument("-i", "--failureip", dest="failureip", help="故障ip")
    moveserver_parser.add_argument("-r", "--recoverip", dest="recoverip", help="恢复ip")
    moveserver_parser.set_defaults(func=moveserver_func)

    #mysql binlog 还原
    recoverbinlog_parser = subparser.add_parser("recoverbinlog", help="binlog还原")
    add_main(recoverbinlog_parser)
    recoverbinlog_parser.add_argument("-i", "--failureip", dest="failureip", help="故障ip")
    recoverbinlog_parser.add_argument("-d", "--recoverDate", dest="recoverDate", help="还原数据库完整备份日期")
    recoverbinlog_parser.add_argument("-f", "--serverfile", dest="serverfile", help="服务器列表文件")
    recoverbinlog_parser.set_defaults(func=recoverbinlog_func)

    #部署游戏服混服的参数列表
    deploymix_parser = subparser.add_parser("deploymix", help="游戏混服部署")
    add_main(deploymix_parser)
    deploymix_parser.add_argument("-s", "--servername", dest="servername", required=True, help="指定游戏服名称，比如:feiliu_1")
    deploymix_parser.add_argument("-m", "--mainserver", dest="mainserver", required=True, help="混服主服名")
    deploymix_parser.add_argument("-r", "--restart", dest="restart", choices=["yes", "no"], help="部署游戏混服是否重启游戏服")
    deploymix_parser.add_argument("-t", "--title", dest="title", help="游戏www标题")
    deploymix_parser.add_argument("-u", "--gameurl", dest="gameurl", help="游戏域名")
    deploymix_parser.add_argument("-a", "--asturl", dest="asturl", help="游戏域名对应的ast的cname域名")
    deploymix_parser.add_argument("-k", "--skipcheck", dest="skipcheck", action="store_true", help="布服前不进行游戏是否存在检查")
    deploymix_parser.set_defaults(func=deploymix_func)

    #重设清档时间的参数列表
    resetcleartime_parser = subparser.add_parser("resetcleartime", help="重设清档时间")
    add_main(resetcleartime_parser)
    resetcleartime_parser.add_argument("-s", "--servername", dest="servername", required=True, help="指定游戏服名称，比如:feiliu_1")
    resetcleartime_parser.add_argument("-C", "--cleartime", dest="cleartime", required=True, help="游戏清档时间")
    resetcleartime_parser.add_argument("-S", "--starttime", dest="starttime", required=True, help="游戏开服时间")
    resetcleartime_parser.set_defaults(func=resetcleartime_func)
    
    #添加联运白名单
    addwhiteip_parser = subparser.add_parser("addwhiteip", help="添加联运白名单")
    add_main(addwhiteip_parser)
    addwhiteip_parser.add_argument("-y", "--yx", dest="yx", required=True, help="需要添加白名单的yx")
    addwhiteip_parser.add_argument("-i", "--iplist", dest="iplist", required=True, help="白名单列表")
    addwhiteip_parser.set_defaults(func=addwhiteip_func)
    
    #游戏模板生成的参数列表
    template_parser = subparser.add_parser("template", help="游戏模板生成")
    add_main(template_parser)
    template_parser.add_argument("-s", "--servername", dest="servername", required=True, help="指定游戏服名称，比如:feiliu_1")
    template_parser.add_argument("-m", "--mainServername", dest="mainServername", help="指定游戏服主服名称，比如:feiliu_1")
    template_parser.add_argument("-i", "--ip", dest="ip", help="ip地址，比如:1.1.1.1")
    template_parser.add_argument("-p", "--port", dest="port", default=22, type=int, help="ssh连接端口号，默认22")
    template_parser.add_argument("-t", "--templatetype", dest="templatetype", required=True, help="模板生成类型，[all, sql, common, gametemplate, www, properties, nginx]")
    template_parser.set_defaults(func=template_func)
    
    #游戏所有模板生成的参数列表
    alltemplate_parser = subparser.add_parser("alltemplate", help="游戏所有模板生成")
    add_main(alltemplate_parser)
    alltemplate_parser.add_argument("-t", "--templatetype", dest="templatetype", required=True, help="模板生成类型，[all, sql, common, gametemplate, www, properties, nginx]")
    alltemplate_parser.set_defaults(func=alltemplate_func)
    
    #游戏服列表的参数列表
    serverlist_parser = subparser.add_parser("serverlist", help="获取服务器列表")
    add_main(serverlist_parser)
    add_serverlist(serverlist_parser)
    serverlist_parser.set_defaults(func=serverlist_func)
    
    #手游前端测试环境动态更新
    mobileWwwTestUpdate_parser = subparser.add_parser("mobileWwwTestUpdate", help="手游前端测试环境动态更新")
    add_main(mobileWwwTestUpdate_parser)
    mobileWwwTestUpdate_parser.add_argument("-v", "--version", dest="version", required=True, help="更新的版本")
    mobileWwwTestUpdate_parser.add_argument("-t", "--updateType", dest="updateType", required=True, choices=["appstore", "appstore64", "jailbreak", "all"], help="更新类型，比如:appstore")
    mobileWwwTestUpdate_parser.add_argument("-H", dest="hd", action="store_true", help="是否高清模式")
    mobileWwwTestUpdate_parser.set_defaults(func=mobileWwwTestUpdate_func)
    
    #手游前端正式环境动态更新
    mobileWwwUpdate_parser = subparser.add_parser("mobileWwwUpdate", help="手游前端正式环境更新")
    add_main(mobileWwwUpdate_parser)
    mobileWwwUpdate_parser.add_argument("-v", "--version", dest="version", required=True, help="更新的版本")
    mobileWwwUpdate_parser.add_argument("-t", "--updateType", dest="updateType", required=True, choices=["appstore", "appstore64", "jailbreak", "all"], help="更新类型，比如:appstore")
    mobileWwwUpdate_parser.add_argument("-H", dest="hd", action="store_true", help="是否高清模式")
    mobileWwwUpdate_parser.set_defaults(func=mobileWwwUpdate_func)
    
    #游戏后端更新
    update_parser = subparser.add_parser("update", help="游戏更新")
    add_main(update_parser)
    #update_parser.add_argument("--sqlOrNot", dest="sqlOrNot", choices=["yes", "no"], help="是否执行sql，必须为{yes|no}")
    update_parser.add_argument("--sqlFile", dest="sqlFile", help="如果需要执行sql，指定sql文件名称")
    #update_parser.add_argument("--backendChangeOrNot", dest="backendChangeOrNot", choices=["yes", "no"], help="是否需要修改游戏服后端目录，必须为{yes|no}")
    #update_parser.add_argument("--backendUpload", dest="backendUpload", choices=["yes", "no"], help="是否需要上传后端，必须为{yes|no}")
    update_parser.add_argument("--backendName", dest="backendName", help="如果要更改后端目录或者上传后端包，指定后端目录名称")
    update_parser.add_argument("--frontName", dest="frontName", help="前端更新目录名称")
    update_parser.add_argument("--executeVersionList", dest="executeVersionList", help="指定需要更新的版本号，多个使用', '隔开，比如:1.1.1.1, 1.1.1.0")
    update_parser.add_argument("--executeDbVersionList", dest="executeDbVersionList", help="指定需要更新的数据库版本号，多个使用', '隔开，比如:1.1.1.1, 1.1.1.0")
    update_parser.add_argument("--resourceDir", dest="resourceDir", help="放置更新需要的文件的ftp地址目录")
    update_parser.add_argument("--replaceFile", dest="replaceFile", help="需要替换的文件列表，多个以', '隔开，比如:backend/apps/job.properties=job.properties|...")
    update_parser.add_argument("--addFile", dest="addFile", help="需要添加的文件列表，多个以', '隔开，比如:backend/apps/=job.properties|...")
    update_parser.add_argument("--addContent", dest="addContent", help="添加配置内容列表，多个以', '隔开，比如:backend/apps/job.properties=add_job.properties|...")
    update_parser.add_argument("--specialScript", dest="specialScript", help="额外更新脚本在rundeck的绝对路径")
    update_parser.add_argument("--executeFirst", dest="executeFirst", choices=["yes", "no"], help="如果有额外更新的脚本, 指定执行\时间, yes:停服后即执行脚本, no:更新完毕后执行该脚本")
    update_parser.add_argument("--restart", dest="restart", choices=["yes", "no"], help="是否重启游戏服")
    add_serverlist(update_parser)
    update_parser.set_defaults(func=update_func)

    #hotswap动更
    hotswap_parser = subparser.add_parser("hotswap", help="hotswap动更")
    add_main(hotswap_parser)
    hotswap_parser.add_argument("-t", "--hotswapType", dest="hotswapType", choices=["update", "remote"], required=True, help="动更类型")
    hotswap_parser.add_argument("-k", "--keyword", dest="keyword", required=True, help="动更关键字")
    hotswap_parser.add_argument("-b", "--backend", dest="backend", help="备用后端目录")
    add_serverlist(hotswap_parser)
    hotswap_parser.set_defaults(func=hotswap_func)
    
    #游戏服重启
    restart_parser = subparser.add_parser("restart", help="游戏服重启")
    add_main(restart_parser)
    restart_parser.add_argument("-t", "--restartType", dest="restartType", required=True, choices=["start", "stop", "restart"], help="重启类型")
    add_serverlist(restart_parser)
    restart_parser.set_defaults(func=restart_func)

    #资产获取
    assetrooms_parser = subparser.add_parser("assetrooms", help="资产查询")
    add_main(assetrooms_parser)
    assetrooms_parser.add_argument("-r", "--gamerooms", dest="gamerooms", help="机房中文名称, eg:泰国机房")
    assetrooms_parser.add_argument("-t", "--projecttag", dest="projecttag", help="项目表示，eg:gcld_th")
    assetrooms_parser.set_defaults(func=assetrooms_func)
    
    #手游前段测试环境ip添加
    mobileWwwTestEnvironmentAdd_parser = subparser.add_parser("mobileWwwTestEnvAdd", help="手游前端测试环境ip添加")
    add_main(mobileWwwTestEnvironmentAdd_parser)
    mobileWwwTestEnvironmentAdd_parser.add_argument("-i", "--ip", dest="ip", required=True, help="测试ip")
    mobileWwwTestEnvironmentAdd_parser.set_defaults(func=mobileWwwTestEnvAdd_func)

    #手游前段测试环境ip删除
    mobileWwwTestEnvironmentDel_parser = subparser.add_parser("mobileWwwTestEnvDel", help="手游前端测试环境ip删除")
    add_main(mobileWwwTestEnvironmentDel_parser)
    mobileWwwTestEnvironmentDel_parser.add_argument("-i", "--ip", dest="ip", required=True, help="测试ip")
    mobileWwwTestEnvironmentDel_parser.set_defaults(func=mobileWwwTestEnvDel_func)

    #全服执行sql
    allGameExecSql_parser = subparser.add_parser("allGameExecSql", help="全服执行sql")
    add_main(allGameExecSql_parser)
    allGameExecSql.arg_init(allGameExecSql_parser)
    add_serverlist(allGameExecSql_parser)
    allGameExecSql_parser.set_defaults(func=allGameExecSql.run)

    #游戏sql执行
    gameSqlExecute_parser = subparser.add_parser("gameSqlExecute",help="游戏sql执行")
    add_main(gameSqlExecute_parser)
    gameSqlExecute.arg_init(gameSqlExecute_parser)
    gameSqlExecute_parser.set_defaults(func=gameSqlExecute.run)

    #testEnvRelease  Created by Xiaoyu
    testEnvRelease_parser = subparser.add_parser("testEnvRelease", help="测试环境发布集合")
    add_args_for_testEnvRelease(testEnvRelease_parser)
    testEnvRelease_parser.set_defaults(func=testEnvRelease_func)
 
    #测试中控更新  Created by Xiaoyu
    testEnvPayProxyRelease_parser = subparser.add_parser("testEnvPayProxyRelease", help="测试充值中控更新")
    add_args_for_testEnvPayProxyRelease(testEnvPayProxyRelease_parser)
    testEnvPayProxyRelease_parser.set_defaults(func=testEnvPayProxyRelease_func)

    testEnvModifyConfig_parser = subparser.add_parser("testEnvModifyConfig", help="测试环境配置文件修改")
    add_args_for_testEnvModifyConfig(testEnvModifyConfig_parser)
    testEnvModifyConfig_parser.set_defaults(func=testEnvModifyConfig_func)

 ####################################################################
    options = parser.parse_args() 

    global game, language, action
    game = options.game
    language = options.language
    action = options.action
    checkArg(options.game, "游戏项目不能为空")
    checkArg(options.language, "游戏语言不能为空")
    checkArg(options.action, "操作类型不能为空")
    config.read("%s/%s.conf"%(conf, options.game))
    checkSection(config, options.language)
    state.game = game
    state.language = language
    state.action = action
    state.options = options

    options.func(options)

if __name__ == "__main__" :
    arg_init()
