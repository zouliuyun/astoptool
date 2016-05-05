#!/bin/bash
while getopts ":g:s:d:" optname
    do
        case "$optname" in
             "g")
              game="$OPTARG"
              ;;
             "s")
              server_flag="$OPTARG"
              ;;
             "d")
              dnsname="$OPTARG"
              ;;
        esac
done
server_lys=$(echo $server_flag|cut -d'_' -f1)
server_id=$(echo $server_flag|cut -d'_' -f2)
########
servername=${game}_${server_flag}
#################################################################     修改配置     #################################################
#.修改跨服国战显示标志
cd /app/$servername/backend/apps
cname=`grep -E "^([a-z0-9]*\.)?showservername" $server_lys.properties |sed -r -e "s/^([a-z0-9]*.)?showservername = //g;s/ *$/$server_id/g"`
server_cname=$(echo $cname|sed -e 's/\\/\\\\/g')
sed -i 's/\(^[a-z0-9]*\.\?serverchinesename = \).*/\1'$server_cname'/g' server.properties
#联运配置文件修改
sed -i "s/\(^[a-z0-9]*\.\?game.url = https\?:\/\/\)[^\/]*\(.*\)/\1${dnsname}\2/g" ${server_lys}.properties
sed -i "s/\(^[a-z0-9]*\.\?servername = \).*/\1${server_lys}/g" ${server_lys}.properties
sed -i "s/\(^[a-z0-9]*\.\?serverid = \).*/\1s$server_id/g" ${server_lys}.properties
sed -i "s/\(^[a-z0-9]*\.\?serverids = \).*/\1S$server_id/g" ${server_lys}.properties
#修改运营商标示
sed -i "s/\(^[a-z0-9]*\.\?yx = \).*/\1${server_lys}/g" server.properties
#修改战报路径
sed -i "s/\(^[a-z0-9]*\.\?report.linux.path.*app\).*[0-9]\(.*\)/\1\/${servername}\2/g" server.properties
#修改跨服战唯一标示key
sed -i "s/\(^[a-z0-9]*\.\?serverkey = \).*/\1${servername}/g" server.properties
