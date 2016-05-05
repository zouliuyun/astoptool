#!/bin/bash
while getopts ":g:m:s:d:" optname
    do
        case "$optname" in
             "g")
              game="$OPTARG"
              ;;
             "m")
              Main_server="$OPTARG"
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
#修改游戏中的配置
cd /app/$Main_server/backend/apps
#....................修改跨服国战显示标志...........................
cname=`grep -E "^([a-z0-9]*\.)?showservername" $server_lys.properties |sed -e "s/gcld.showservername = //g;s/ *$/$server_id/g"`
server_cname=$(echo $cname|sed -e 's/\\/\\\\/g')
sed -i 's/\(^[a-z0-9]*\.\?serverchinesename = \).*/\1'$server_cname'/g' server.properties
#sed -i "s/\(gcld.game.url = \).*/\1http:\/\/$dnsname/g" ${server_lys}.properties
sed -i "s/\(^[a-z0-9]*\.\?game.url = https\?:\/\/\)[^\/]*\(.*\)/\1${dnsname}\2/g" ${server_lys}.properties
sed -i "s/\(^[a-z0-9]*\.\?servername = \).*/\1${server_lys}/g" ${server_lys}.properties
sed -i "s/\(^[a-z0-9]*\.\?serverid = \).*/\1s$server_id/g" ${server_lys}.properties
sed -i "s/\(^[a-z0-9]*\.\?serverids = \).*/\1S$server_id/g" ${server_lys}.properties
#修改运营商标示
sed -i "s/\(^[a-z0-9]*\.\?yx = .*\)/\1,${server_lys}/g" server.properties
