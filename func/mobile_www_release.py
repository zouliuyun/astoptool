# -*- coding:utf-8 -*-
"""
新的手游前端动更脚本

    为什么会把测试环境动更跟正式环境动更写在一个脚本里面？
    答：手游的前端测试环境跟正式环境并不是完全独立分开，而是耦合度很高。正式环境上线的时候是从测试环境直接复制差异包到正式的前端目录。
    因此考虑在脚本里面分两个代码块来管理，以实现尽可能复用代码，简化代码维护量。
    

.. 名词解释:
    在前端动更的环境里面有太多地方可以用type这个词来表示，也因为如此，会让人迷惑。这个脚本里完全抛弃了type。
    以下举一个示例：
        /app/tjmob_www/jailbreak/version.lua
        /app/tjmob_www/3.6.1.2/res_64/3.6.1.2_30lv.zip

        其中jailbrek 在脚本内称为scope
            res_64 在脚本内称为inner_scope
        
.. 关于mode:
    目前我们前端目录结构有两种，tjmob是一种，其他的是另一种。tjmob之前设计的时候并未跟gcmob统一。
    所以才会存在mode参数，mode参数默认是1，tjmob需要设置为2。

2015-07-15 Xiaoyu Init create.
"""
from __future__ import print_function, with_statement

import sys
import time
import re
import os

from fabric.api import env, lcd, local, cd, run, put, execute, quiet, hosts, settings, hide

from bible.utils import set_fabric_common_env, TIMESTAMP, RSYNC
from bible.config_reader import ConfigReader


def version_tuple(v):
    return tuple(map(int, (v.split("."))))

def sorted_versions(versions, reverse=False):
    v_touples = [version_tuple(each) for each in versions]
    sorted_v_tuples = sorted(v_touples, reverse=reverse)
    return ['.'.join((str(v) for v in each)) for each in sorted_v_tuples]

def remote_file_exists(file):
    with quiet():
        return run('test -f "{}"'.format(file)).succeeded

def remote_dir_exists(file):
    with quiet():
        return run('test -d "{}"'.format(file)).succeeded

def remote_mkdir(dir):
    run('[[ -d {0} ]] || mkdir -p {0}'.format(dir))
    
def md5_verify(remote_script_dir, lua_file, resource_dir):
    """
    这里面的参数是相对路径，修改的话需要小心。请在with cd(dir): 下调用此函数。

    Example:
        python /app/opbak/make_diff_3/make_diff.py --verify-md5 --resource-dir 3.6.1.0/res -f 3.6.1.0/res/res.lua
    """
    run('''python {remote_script_dir}/make_diff.py --verify-md5 --resource-dir {resource_dir} -f {lua_file}'''.format(remote_script_dir=remote_script_dir, resource_dir=resource_dir, lua_file=lua_file))

def version_regex_check(version):
    if not re.match(r'[0-9]+(\.[0-9]+){3}', version):
        raise Exception("版本号:{} 不符合规则, 示例: 1.5.3.11".format(version))
 
def list_inner_scopes(root_dir, version):
    with cd('{}/{}'.format(root_dir, version)), hide('running', 'stdout'):
        result = run('''find ./ -mindepth 1 -maxdepth 1 -type d -print''')  
    return [each.lstrip('./') for each in result.splitlines()]

def list_existed_versions(root_dir):
    """
    列出前端目录下已经存在着的版本
    """
    with cd(root_dir), hide('running', 'stdout'):
        result = run('''( find ./ -mindepth 1 -maxdepth 1 -type d -print |grep --color=never -E '[0-9]+(\.[0-9]+){3}\\b' ) || echo "no_version_found"''')  

    if result == "no_version_found":
        return []
    else:
        return [each.lstrip('./') for each in result.splitlines()]

def filter_need_diff_versions(root_dir, start_zip_version, reverse=True):
    """
    筛选出需要做差异包的有哪些版本
    """
    existed_versions = list_existed_versions(root_dir)

    #start_zip_version版本之前的不做差异包
    if start_zip_version:
        _need_diff_versions = [each for each in existed_versions if version_tuple(each) >= version_tuple(start_zip_version)] 
    else:
        _need_diff_versions = existed_versions

    return sorted_versions(_need_diff_versions, reverse=reverse)
 
def make_diff(remote_script_dir, diff_from_lua, diff_to_lua, resource_dir, dest):
    """
    这里面的参数是相对路径，修改的话需要小心。请在with cd(dir): 下调用此函数。

    Example:
        /app/opbak/make_diff_3/make_diff.py --resource-dir 3.6.1.0/res --diff-from 3.6.0.9/res/res.lua --diff-to 3.6.1.0/res/res.lua --dest /app/opbak/make_diff_20150909_xxxxx/3.6.1.0,/app/opbak/make_diff_20150909_xxxxx/3.6.1.0.zip
    """
    with hide('running', 'stdout'):
        run('''python {remote_script_dir}/make_diff.py --resource-dir {resource_dir} --diff-from {diff_from_lua} --diff-to {diff_to_lua} --dest {dest}'''.format(remote_script_dir=remote_script_dir, resource_dir=resource_dir, diff_from_lua=diff_from_lua, diff_to_lua=diff_to_lua, dest=dest))

    #计算出差异包对应的.lua文件
    _zipfile = dest.split(',')[0]
    zipfile = _zipfile.rstrip('.zip')
    zip_lua = '{}.lua'.format(zipfile)
    with hide('running', 'stdout'):
        file_size = run('stat --printf="%s" {}'.format(zipfile))
        md5 = run("md5sum {} | awk '{{print $1}}'".format(zipfile)).strip('\n')
        run('''echo -ne 'local updateZipSize = {{}}\nupdateZipSize.value = {file_size}\nupdateZipSize.md5 = "{md5}"\nreturn updateZipSize' >{zip_lua}'''.format(file_size=file_size, md5=md5, zip_lua=zip_lua))

def copy_diff(root_dir_test, root_dir_prod, dest):
    """
    拷贝测试环境中的差异包到生产环境
    """
    dests = dest.split(',')
    for each_dest in dests:
        with hide('running', 'stdout'):
            run('cp -f {0}/{2} {1}/{2}'.format(root_dir_test, root_dir_prod, each_dest))

def rsync_to_backup(game, region):
    print("等待同步资源目录到备用服务器...")
    sys.stdout.flush()
    time.sleep(30)
    config = ConfigReader(game, region)
    rsync_module = config.get("rsync_module")
    rsync_root = config.get("rsync_root")
    rsync_backup_ip = config.get("rsync_backup_ip")

    if rsync_module == "" or rsync_root == "" or rsync_backup_ip == "" :
        raise Exception('rsync config is not proper in the game config file')

    with cd(rsync_root), settings(user='root'), hide("stdout"):
        run('''rsync -art -R --delete --out-format="%n" --password-file=/etc/rsyncd.secret ./ {}::{}'''.format(rsync_backup_ip, rsync_module))
     
    #for i in range(3):
    #    with cd(rsync_root), settings(user='root'), hide("stdout"):
    #        out = run('''rsync -art -R --dry-run --delete --out-format="%n" --password-file=/etc/rsyncd.secret ./ {}::{}'''.format(rsync_backup_ip, rsync_module), timeout=120)
    #        
    #    if out.strip() != "":
    #        print("资源暂未完全同步到备用下载点, 等待60s后重新检查...")
    #        sys.stdout.flush()
    #        time.sleep(60)
    #    else:
    #        print("资源同步完毕!")
    #        break
    #else:
    #    print("[WARNING]: 资源有未同步的情况, 30s之后将会更新version.lua, 或者手动终止任务!!!!!!!")
    #    sys.stdout.flush()
    #    time.sleep(30)
 
def test_env_mobile_www_release(game, region, version, scopes, root_dir, ip, start_zip_version, mode=1):

    def scope_check(remote_temp_dir, scope, version):
        version_lua = '{}/{}/version.lua'.format(remote_temp_dir, scope)
        if not remote_file_exists(version_lua):
            raise Exception('无法在{0}.zip文件中找到{1}/version.lua, 请确认scope中的{1}是否填写正确'.format(scope, version))
    
        version_inside_zip = run("grep --color=never 'sys_version.game' %s/%s/version.lua"%(remote_temp_dir, scope)).split('"')[1]
        if version_inside_zip != version :
            raise Exception("很抱歉, 本次即将更新的版本为: {}, 你所上传的zip包中的version为: {}, 不匹配".format(version, version_inside_zip))

    @hosts(ip)
    def _test_env_mobile_www_release():
        """
        Inner Fabric task 
        """
        ftp_resource_dir = "/app/online/{}/frontend/{}/{}".format(game, region, version)
        remote_script_dir = "/app/opbak/mobile_www_scripts_{}".format(TIMESTAMP)
        remote_temp_dir = "/app/opbak/mobile_www_test_release/{}/{}/{}".format(game, region, version)
        remote_backup_dir = "/app/opbak/mobile_www_test_backup/{}_{}_{}".format(game, region, TIMESTAMP)

        #本地检查md5
        with lcd(ftp_resource_dir):
            local("dos2unix md5.txt >/dev/null 2>&1")
            local("chown virtual_user.virtual_user md5.txt")
            local("md5sum -c md5.txt >/dev/null")
    
        #新建远程临时资源目录
        if remote_dir_exists(remote_temp_dir):
            run('mv {0} {0}.rb{1}'.format(remote_temp_dir, TIMESTAMP))
        remote_mkdir(remote_temp_dir)
    
        #上传zip包跟md5.txt
        version_zip_file = '{}.zip'.format(version)
        print('正在上传 {}...'.format(version_zip_file))
        sys.stdout.flush()
        with lcd(ftp_resource_dir):
            put(version_zip_file, remote_temp_dir)
            put('md5.txt', remote_temp_dir)
    
        #再次检查md5
        with cd(remote_temp_dir):
            run('dos2unix md5.txt')
            run('md5sum -c md5.txt')
            run("unzip -o -q {}".format(version_zip_file))
    
        for each_scope in scopes:
            scope_check(remote_temp_dir, each_scope, version)

        #生成差异包的python脚本
        make_diff_py = '/app/opbin/work/bible/func/make_diff.py'
        remote_mkdir(remote_script_dir)
        put(make_diff_py, remote_script_dir)

        #校验res.lua所包含的文件md5值跟文件实际md5值的一致性
        res_to_verify = ['res.lua', 'res_preview.lua']
        _inner_scopes = list_inner_scopes(remote_temp_dir, version)
        for each_scope in _inner_scopes:
            for each_res_lua in res_to_verify:
                lua_file = '{}/{}/{}/{}'.format(remote_temp_dir, version, each_scope, each_res_lua)
                if remote_file_exists(lua_file):
                    resource_dir = os.path.dirname(lua_file)
                    md5_verify(remote_script_dir, lua_file, resource_dir)

        #备份
        with cd(root_dir):
            if remote_dir_exists(version):
                run('mkdir -p {}'.format(remote_backup_dir))
                run('mv {} {}/'.format(version, remote_backup_dir))
                for each_scope in scopes:
                    if remote_dir_exists(each_scope):
                        run('cp -r {} {}/'.format(each_scope, remote_backup_dir)) 
                    else:
                        print('[Warning] {root_dir}/目录下不存在{scope}, 默认这是{scope}的第一次发布。'.format(root_dir=root_dir, scope=each_scope))
        
        with cd(remote_temp_dir):
            run('cp -r {} {}/'.format(version, root_dir))
    
        need_diff_versions = filter_need_diff_versions(root_dir, start_zip_version)
   
        #处理完整版版本之间的差异包
        print('开始处理完整版的差异包...')
        for each_version in need_diff_versions:
            if version_tuple(each_version) >= version_tuple(version):
                print('跳过{}, 不需要版本差异包'.format(each_version))
            else:
                if mode == 2:
                    _inner_scopes = list_inner_scopes(root_dir, each_version)
                    for each_scope in _inner_scopes:
                        diff_from_lua = '{}/{}/res.lua'.format(each_version, each_scope)
                        with cd(root_dir):
                            if remote_file_exists(diff_from_lua):
                                diff_to_lua = '{}/{}/res.lua'.format(version, each_scope)
                                resource_dir = '{}/{}'.format(version, each_scope)
                                dest = '{0}/{1}/{2}.zip,{0}/{1}/{2}'.format(each_version, each_scope, version)
                                print('正在生成 {} 完整版的差异包 ==> {} ...'.format(each_version, dest.replace(',', ', ')))
                                sys.stdout.flush()
                                make_diff(remote_script_dir, diff_from_lua, diff_to_lua, resource_dir, dest)
                else:
                    diff_from_lua = '{}/res.lua'.format(each_version)
                    with cd(root_dir):
                        if remote_file_exists(diff_from_lua):
                            diff_to_lua = '{}/res.lua'.format(version)
                            resource_dir = version
                            dest = '{0}/{1}.zip,{0}/{1}'.format(each_version, version)
                            print('正在生成 {} 完整版的差异包 ==> {} ...'.format(each_version, dest.replace(',', ', ')))
                            sys.stdout.flush()
                            make_diff(remote_script_dir, diff_from_lua, diff_to_lua, resource_dir, dest)
 
        #处理预览版版本之间的差异包
        print('开始处理预览版的差异包...')
        for each_version in need_diff_versions:
            if version_tuple(each_version) >= version_tuple(version):
                print('跳过{}, 不需要版本差异包'.format(each_version))
            else:
                if mode == 2:
                    _inner_scopes = list_inner_scopes(root_dir, each_version)
                    for each_scope in _inner_scopes:
                        diff_from_lua = '{}/{}/res_preview.lua'.format(each_version, each_scope)
                        with cd(root_dir):
                            if remote_file_exists(diff_from_lua):
                                diff_to_lua = '{}/{}/res_preview.lua'.format(version, each_scope)
                                resource_dir = '{}/{}'.format(version, each_scope)
                                dest = '{0}/{1}/{2}_preview.zip,{0}/{1}/{2}_preview'.format(each_version, each_scope, version)
                                print('正在生成 {} 预览版的差异包 ==> {} ...'.format(each_version, dest.replace(',', ', ')))
                                sys.stdout.flush()
                                make_diff(remote_script_dir, diff_from_lua, diff_to_lua, resource_dir, dest)
                else:
                   diff_from_lua = '{}/res_preview.lua'.format(each_version)
                   with cd(root_dir):
                       if remote_file_exists(diff_from_lua):
                           diff_to_lua = '{}/res_preview.lua'.format(version)
                           resource_dir = version
                           dest = '{0}/{1}_preview.zip,{0}/{1}_preview'.format(each_version, version)
                           print('正在生成 {} 预览版的差异包 ==> {} ...'.format(each_version, dest.replace(',', ', ')))
                           sys.stdout.flush()
                           make_diff(remote_script_dir, diff_from_lua, diff_to_lua, resource_dir, dest)
     
        #处理预览版跟完整版的差异包
        print('开始处理预览版跟完整版的差异包...')
        if mode == 2:
            _inner_scopes = list_inner_scopes(root_dir, version)
            for each_scope in _inner_scopes:
                diff_from_lua = '{}/{}/res_preview.lua'.format(version, each_scope)
                with cd(root_dir):
                    if remote_file_exists(diff_from_lua):
                        diff_to_lua = '{}/{}/res.lua'.format(version, each_scope)
                        resource_dir = '{}/{}'.format(version, each_scope)
                        dest = '{0}/{1}/{2}_30lv.zip,{0}/{1}/{2}_30lv'.format(version, each_scope, version)
                        print('正在生成 {}_30lv 差异包 ==> {} ...'.format(version, dest.replace(',', ', ')))
                        sys.stdout.flush()
                        make_diff(remote_script_dir, diff_from_lua, diff_to_lua, resource_dir, dest)
        else:
            diff_from_lua = '{}/res_preview.lua'.format(version)
            with cd(root_dir):
                if remote_file_exists(diff_from_lua):
                    diff_to_lua = '{}/res.lua'.format(version)
                    resource_dir = version
                    dest = '{0}/{1}_30lv.zip,{0}/{1}_30lv'.format(version, version)
                    print('正在生成 {}_30lv 差异包 ==> {} ...'.format(version, dest.replace(',', ', ')))
                    sys.stdout.flush()
                    make_diff(remote_script_dir, diff_from_lua, diff_to_lua, resource_dir, dest)
    
        with cd(remote_temp_dir):
            for each_scope in scopes:
                run('cp -rf {} {}/'.format(each_scope, root_dir))
    
        #清理FTP上的目录和文件
        local("rm -rf /app/online/{}/frontend/{}/{}".format(game, region, version))

    execute(_test_env_mobile_www_release)

def prod_env_mobile_www_release(game, region, version, scopes, root_dir_prod, root_dir_test, ip, start_zip_version="", mode=1):

    @hosts(ip)
    def _prod_env_mobile_www_release():
        #检查测试环境中在用的版本与即将更新的版本是否一致
        with cd(root_dir_test):
            for each_scope in scopes:
                _result = run('grep --color=never sys_version.game {}/version.lua'.format(each_scope))
                if len(_result.splitlines()) != 1:
                    raise Exception('[ERROR] More than one line returned when do "grep sys_version.game {}/version.lua".'.format(each_scope))
                test_env_current_version = _result.split('"')[1]
                if test_env_current_version != version:
                    raise Exception("测试环境中 {} 的sys_version.game为:{}, 本次即将更新的版本为:{}, 不匹配".format(each_scope, test_env_current_version, version))

        #备份
        remote_backup_dir = "/app/opbak/mobile_www_prod_backup/{}_{}_{}".format(game, region, TIMESTAMP)
        remote_mkdir(remote_backup_dir)
        with cd(root_dir_prod):
            if remote_dir_exists(version):
                run('mv {} {}/'.format(version, remote_backup_dir))
            for each_scope in scopes:
                if remote_dir_exists(each_scope):
                    run('cp -r {} {}/'.format(each_scope, remote_backup_dir)) 
                else:
                    print('[Warning] {root_dir}/目录下不存在{scope}, 默认这是{scope}的第一次发布。'.format(root_dir=root_dir_prod, scope=each_scope))
 

        #拷贝新版本的目录到生产环境
        with cd(root_dir_test):
            run('cp -r {} {}/'.format(version, root_dir_prod))
    
        need_diff_versions = filter_need_diff_versions(root_dir_prod, start_zip_version, reverse=False)
   
        #处理完整版版本之间的差异包
        print('开始将完整版的差异包从测试环境拷贝到生产环境...')
        for each_version in need_diff_versions:
            if version_tuple(each_version) >= version_tuple(version):
                print('跳过{}, 不需要版本差异包'.format(each_version))
            else:
                if mode == 2:
                    _inner_scopes = list_inner_scopes(root_dir_prod, each_version)
                    for each_scope in _inner_scopes:
                        diff_from_lua = '{}/{}/{}/res.lua'.format(root_dir_prod, each_version, each_scope)
                        if remote_file_exists(diff_from_lua):
                            dest = '{0}/{1}/{2}.lua,{0}/{1}/{2}.zip,{0}/{1}/{2}'.format(each_version, each_scope, version)
                            print('正在拷贝 {} 完整版的差异包 ==> {} ...'.format(each_version, dest.replace(',', ', ')))
                            sys.stdout.flush()
                            copy_diff(root_dir_test, root_dir_prod, dest)
                else:
                   diff_from_lua = '{}/{}/res.lua'.format(root_dir_prod, each_version)
                   if remote_file_exists(diff_from_lua):
                       dest = '{0}/{1}.lua,{0}/{1}.zip,{0}/{1}'.format(each_version, version)
                       print('正在拷贝 {} 完整版的差异包 ==> {} ...'.format(each_version, dest.replace(',', ', ')))
                       sys.stdout.flush()
                       copy_diff(root_dir_test, root_dir_prod, dest)
    
        #处理预览版版本之间的差异包
        print('开始将预览版的差异包从测试环境拷贝到生产环境...')
        for each_version in need_diff_versions:
            if version_tuple(each_version) >= version_tuple(version):
                print('跳过{}, 不需要版本差异包'.format(each_version))
            else:
                if mode == 2:
                    _inner_scopes = list_inner_scopes(root_dir_prod, each_version)
                    for each_scope in _inner_scopes:
                        diff_from_lua = '{}/{}/{}/res_preview.lua'.format(root_dir_prod, each_version, each_scope)
                        if remote_file_exists(diff_from_lua):
                            dest = '{0}/{1}/{2}_preview.lua,{0}/{1}/{2}_preview.zip,{0}/{1}/{2}_preview'.format(each_version, each_scope, version)
                            print('正在拷贝 {} 预览版的差异包 ==> {} ...'.format(each_version, dest.replace(',', ', ')))
                            sys.stdout.flush()
                            copy_diff(root_dir_test, root_dir_prod, dest)
                else:
                   diff_from_lua = '{}/{}/res_preview.lua'.format(root_dir_prod, each_version)
                   if remote_file_exists(diff_from_lua):
                       dest = '{0}/{1}_preview.lua,{0}/{1}_preview.zip,{0}/{1}_preview'.format(each_version, each_scope, version)
                       print('正在拷贝 {} 预览版的差异包 ==> {} ...'.format(each_version, dest.replace(',', ', ')))
                       sys.stdout.flush()
                       copy_diff(root_dir_test, root_dir_prod, dest)
    
        #等待备份服务器同步完毕, 再接着更新
        conf_wait_rsync = ConfigReader(game, region)
        if conf_wait_rsync.has_option("mobile_www_wait_rsync"):
            wait_rsync = conf_wait_rsync.getboolean("mobile_www_wait_rsync")
            if wait_rsync:
                rsync_to_backup(game, region)

        for each_scope in scopes:
            run('cp -rf {}/{} {}/'.format(root_dir_test, each_scope, root_dir_prod))
    
    execute(_prod_env_mobile_www_release)

def mobile_www_release(game, region, version, scopes, game_env, mode=1):
    """
    总的调度函数，负责读取一些参数，然后传给prod或test的函数

    目前打包任何.zip文件的时候，都同时copy出一份不带zip的压缩包。目的是防止一些小的电信运营商（如长城宽带）缓存.zip文件。
    """

    version_regex_check(version)

    conf = ConfigReader(game, region)

    ip = conf.get("mobile_www_ip")

    if conf.has_option("mobile_www_port"):
        """
        如果前端资源服务器限制了ssh连接端口的话，修改Fabric的连接到该host的端口
        """
        port = conf.getint("mobile_www_port")     
        if port:
            ip = '{}:{}'.format(ip, port)

    if conf.has_option("gateway"):
        """
        配置gateway
        """
        env.gateway = conf.get("gateway")

    if conf.has_option("mobile_www_start_zip_version"):
        start_zip_version = conf.get("mobile_www_start_zip_version")
    else:
        start_zip_version = "0.0.0.0"

    if game_env == 'test':
        root_dir = conf.get("mobile_www_root_test")
        test_env_mobile_www_release(game, region, version, scopes, root_dir, ip, start_zip_version=start_zip_version, mode=mode)
    elif game_env == 'prod':
        root_dir_prod = conf.get("mobile_www_root")
        root_dir_test = conf.get("mobile_www_root_test")
        prod_env_mobile_www_release(game, region, version, scopes, root_dir_prod, root_dir_test, ip, start_zip_version=start_zip_version, mode=mode)


def main(args):
    if args.game and args.language and args.version and args.scope and args.game_env and args.mode:
        set_fabric_common_env()

        game = args.game
        region = args.language
        version = args.version.strip()
        scopes = args.scope.strip().split(',')
        game_env = args.game_env
        mode = args.mode

        mobile_www_release(game, region, version, scopes, game_env, mode=mode)

        print('Done!')

    else:
        print('Use "-h" to see the command-line options')
        sys.exit(1)

def add_mobileWwwRelease_parser(parser):
    """
    添加参数和参数说明
    """
    sub_parser = parser.add_parser("mobileWwwRelease", help="手游前端资源动更v2.0")

    sub_parser.add_argument(
        "-g", 
        "--game", 
        dest="game", 
        required=True, 
        help="game, eg: gcmob"
    )
    sub_parser.add_argument(
        "-l", 
        "--region", 
        dest="language", 
        required=True, 
        help="region, eg: cn, vn, ft"
    )
    sub_parser.add_argument(
        '--env',
        type=str,
        dest='game_env',
        choices=['prod', 'test'],
        help='Production Environment or Test Environment?'
    )
    sub_parser.add_argument(
        '--mode',
        type=int,
        dest='mode',
        choices=[1, 2],
        default=1,
        help='different game should have different mode'
    )
    sub_parser.add_argument(
        '-t',
        type=str,
        dest='version',
        help='mobile frontend version, eg: 3.0.0.12'
    )
    sub_parser.add_argument(
        '-s',
        type=str,
        dest='scope',
        help='the scope you want to release, eg: jailbreak,appstore'
    )
    sub_parser.set_defaults(func=main)

