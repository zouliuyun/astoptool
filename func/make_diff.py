#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
一个尽可能最小化的通用的制作差异包的脚本工具。
resource_dir: 新版本二进制资源的目录
将打出从diff_from到diff_to需要的差异包，保存在dest的位置（dest可以包含多个位置）

注意:
    指定目录的时候绝对路径不会有问题，但是会显得冗长。相对路径使用的时候一定需要注意运行脚本时候的当前目录!

Example:
    1. 制作差异包
        cd /path/to/mobile_www_test_root/ && python /app/opbak/make_diff_3/make_diff.py --resource-dir 3.6.1.0/res --diff-from 3.6.0.9/res/res.lua --diff-to 3.6.1.0/res/res.lua --dest /app/opbak/make_diff_20150909_xxxxx/3.6.1.0,/app/opbak/make_diff_20150909_xxxxx/3.6.1.0.zip

    2. 校验res.lua所包含的文件md5值跟文件实际md5值的一致性
        cd /path/to/mobile_www_root/ && python /app/opbak/make_diff_3/make_diff.py --verify-md5 --resource-dir 3.6.1.0/res -f 3.6.1.0/res/res.lua
 
2015-07-15 Xiaoyu Init create.
"""
from __future__ import with_statement 
from contextlib import contextmanager

import os
import sys
import hashlib
import string
import random
import time
import argparse

@contextmanager
def cd(newdir):
    """
    在with cd(newdir):下使用时, 退出段落后将恢复原来所在的工作目录
    使用这个可以最大程度避免在路径错乱的问题
    """
    prev_dir = os.getcwd()
    try:
        os.chdir(os.path.expanduser(newdir))
        yield
    finally:
        os.chdir(prev_dir)

def md5sum(afile):
    with open(afile, 'rb') as f:
        md5 = hashlib.md5(f.read()).hexdigest()   
    return md5

def random_string(N):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(N))

def verify_file_md5(lua_file, resource_dir):
    """
    验证lua_file所包含的文件信息的一致性
    """
    with open(lua_file, 'rb') as f:
        lines = f.readlines()

    md5_info = {}

    with cd(resource_dir):
        for each_line in lines:
            if 'md5' in each_line:
                parts = each_line.split('"')
                filename = parts[1]
                md5_value = parts[3]

                if filename in md5_info:
                    print('[ERROR] {} found more than once in {}'.format(filename, lua_file))
                    sys.exit(1)

                md5_info[filename] = md5_value 

                if not os.path.exists(filename):
                    print('[ERROR] File: {} NOT exists under {}, but in {}'.format(filename, resource_dir, lua_file))
                    sys.exit(1)

                real_md5 = md5sum(filename)
                if md5_value != real_md5:
                    print('[ERROR] md5 value for {} is wrong.\n It is {} in {},\nbut it should be {}'.format(filename, md5_value, lua_file, real_md5))
                    sys.exit(1)

def lua_to_dict(lua_file):
    """
    将lua_file所包含的文件以及md5值导入到一个字典里
    """
    md5_info = {}

    with open(lua_file) as f:
        lines = f.readlines()

    for each_line in lines:
        if 'md5' in each_line:
            parts = each_line.split('"')
            filename = parts[1]
            md5_value = parts[3]

            if filename in md5_info:
                print('[ERROR] {} found more than once in {}'.format(filename, lua_file))
                sys.exit(1)

            md5_info[filename] = md5_value 
    
    return md5_info

def make_diff_zip(diff_from_lua_file, diff_to_lua_file, resource_dir, dests, verbose=False):
    from os import makedirs
    from tempfile import mkdtemp
    from shutil import copy, move, make_archive, rmtree

    diff_from = lua_to_dict(diff_from_lua_file)
    diff_to = lua_to_dict(diff_to_lua_file)

    diff_filenames = []
    for each_file in diff_to:
    #新增加的文件需要打包, 文件跟老的md5值不一致需要打包
        if each_file not in diff_from:
            diff_filenames.append(each_file)
        elif diff_to[each_file] != diff_from[each_file]:
            diff_filenames.append(each_file)

    if not diff_filenames:
        #如果为空说明新的lua文件所包含的文件在老的里面都存在且一样，所以打不出差异包
        print('[ERROR] No different files from {} to {}'.format(diff_from_lua_file, diff_to_lua_file))
        sys.exit(1)

    timestamp= '{}_{}'.format(time.strftime("%Y%m%d_%H%M%S"), random_string(8))
    diff_dir = '/app/opbak/make_diff/{}'.format(timestamp)
    if verbose:
        print('Temp make diff dir is: {}'.format(diff_dir))
    makedirs(diff_dir)
    tmp_dir = mkdtemp(dir=diff_dir)

    with cd(resource_dir):
        for each_file in diff_filenames:
            copy(each_file, tmp_dir)

    archive_name = '{}/diff'.format(diff_dir)
    archive_file = make_archive(archive_name, 'zip', tmp_dir)

    for each_dest in dests[:-1]:
        copy(archive_file, each_dest)
    move(archive_file, dests[-1]) #最后一次用mv

    if not verbose:
        #如果不是debug模式，就清理掉临时目录
        rmtree(diff_dir)

def main():
    parser = argparse.ArgumentParser(
        description='Make diff zip files for resources.'
    )

    parser.add_argument(
        '--verify-md5',
        dest='verify_md5',
        action='store_true',
        help='verify the md5 value in the .lua file.'
    )
    parser.add_argument(
        '-v',
        '--verbose',
        dest='verbose',
        action='store_true',
        help='increase verbosity'
    )
    parser.add_argument(
        '--diff-from',
        type=str,
        metavar='PATH/TO/FILE',
        dest='diff_from',
        help='the .lua file that you want to diff from.'
    )
    parser.add_argument(
        '--diff-to',
        type=str,
        metavar='PATH/TO/FILE',
        dest='diff_to',
        help='the .lua file that you want to diff from.'
    )
    parser.add_argument(
        '--resource-dir',
        type=str,
        metavar='PATH',
        dest='resource_dir',
        help='the resource dir that contains the diff-to binary files.'
    )
    parser.add_argument(
        '--dest',
        type=str,
        metavar='PATH/TO/FILE',
        dest='dest',
        help='the diff zip file you want to store, eg: some/dir/10.6.5.4.zip,another/dir/to/3.4.4.4_preview'
    )    
    parser.add_argument(
        '-f',
        dest='lua_file',
        type=str,
        metavar='PATH/TO/FILE',
        help='the .lua file, eg: some/dir/a.lua,some/dir/b.lua'
    )
    args = parser.parse_args()

    if args.verify_md5 and args.lua_file and args.resource_dir:
        lua_files = args.lua_file.split(',')
        resource_dir = args.resource_dir
        for each_lua in lua_files:
            verify_file_md5(each_lua, resource_dir)
            print('[PASS] {} verified.'.format(each_lua))

    elif args.diff_from and args.diff_to and args.resource_dir and args.dest:
        diff_from_lua_file = args.diff_from
        diff_to_lua_file = args.diff_to
        resource_dir = args.resource_dir
        dests = args.dest.split(',')
        make_diff_zip(diff_from_lua_file, diff_to_lua_file, resource_dir, dests)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
