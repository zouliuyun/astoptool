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
#修改游戏中的配置
cd /app/$servername/backend/apps
#特殊联运renren，kaixin，xunlei
sed -i "s/\(zzsf2.game.url = \).*/\1http:\/\/$dns_name/g" /app/zzsf2_${server_flag}/backend/apps/${server_name}.properties
sed -i "s/\(zzsf2.serverid = \).*/\1s$server_id/g" /app/zzsf2_${server_flag}/backend/apps/${server_name}.properties
#修改运营商标示
sed -i "s/\(zzsf2.yx = \).*/\1${server_name}/g" /app/zzsf2_${server_flag}/backend/apps/server.properties
#修改服务器唯一id(后端服务唯一标识)
sed -i "s/\(zzsf2.serverkey = \).*/\1zzsf2_${server_flag}/g" /app/zzsf2_${server_flag}/backend/apps/server.properties
#修改战报路径
sed -i "s/\(zzsf2.report.linux.path.*app\).*[0-9]\(.*\)/\1\/zzsf2_${server_flag}\2/g" /app/zzsf2_${server_flag}/backend/apps/server.properties
sed -i "s/\(.*socketServiceUrl value=\"\).*\(\".*\)/\1$WIP:$select_port\2/g" /app/zzsf2_${server_flag}/$wwwdir/Config.xml
