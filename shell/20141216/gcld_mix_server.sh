#!/bin/bash
export JAVA_HOME=/usr/local/jdk;
export LC_ALL="en_US.UTF-8";
export LANG="en_US.UTF-8";
sh /home/astd/.bash_profile
#配置
#中控地址
game=$1
language=$2
title=$3
server_flag=$4
dns_name=$5
Main_server=$6
dns_ip_name=$7 #Config.xml中配置游戏地址，如果为单ip则直接使用ip，如果是多ip则使用游戏域名
download_ip=$8 #资源下载ip
download_url=$9 #资源下载的header
download_port=${10} #资源下载端口
app_restart=${11} #部署混服是否需要重启主服
####################################################################################################################################
exit_error()
{
    if [ $? -ne 0 ];then
        echo "ERROR: $1"
        exit 1
    fi
}
#下载函数
function download()
{
    wget -c -t 10 -T 10 -q --header=HOST:$download_url http://${download_ip}:${download_port}/$game/newserver/${language}/$1
    exit_error "下载${1}失败!"
}
####################################################################################################################################
server_lys=""
server_id=""
if [ "$server_flag" != "" ];
then
    server_lys=`echo $server_flag |head -n 1 |cut -d '_' -f 1`
    server_id=`echo $server_flag |head -n 1 |cut -d '_' -f 2`
else
    echo "server_flag should be given:"
    exit 1
fi

if [ -d /app/$game_${server_flag}/ ];then
    echo "server /app/$game_${server_flag}/ aready exist"
    exit 1
fi
if [ ! -d /app/$Main_server/ ];then
    echo "mix to Main server:$Main_server not exsist"
    exit 1
fi
if [ -d /app/$Main_server/www_${server_flag} ];then
    echo "ERROR: /app/$Main_server/www_${server_flag}已经存在"
    exit 1
fi
if [ -f /app/$Main_server/backend/apps/${server_lys}.properties ];then
    echo "/app/$Main_server/backend/apps/${server_lys}.properties已经存在"
    exit 1
fi
if [ -f /app/nginx/conf/vhost/${game}_${server_flag}.conf ];then
    echo "ERROR: /app/nginx/conf/vhost/${game}_${server_flag}.conf已经存在"
    exit 1
fi
#端口
select_port=""
echo "Auto get Main server port:"
select_port=`grep -H 'port' /app/$Main_server/backend/apps/conf.xml| sed -r 's/.*>([0-9]+).*$/\1/g'`
if [ -z $select_port ];then
    echo "Main server's port is NULL"
    exit 1
else
    echo -e "Use port: $select_port"
fi
http_port=`expr $select_port + 1`

#创建游戏目录解压相应文件
cd /app/$Main_server/
mkdir www_${server_flag} && cd  www_${server_flag}
#创建前端目录
download "www/www_${server_lys}.tgz"
tar -zxf www_${server_lys}.tgz
rm -f www_${server_lys}.tgz
if [ -z "$title" ];then
    echo "NO server title argements!"
else
    sed -i "s/\(<title>\).*\(<\/title>\)/\1 $title \2/g" Main.html
fi
#修改游戏主页标题
sed -i "s/\(.*socketServiceUrl value=\"\).*\(\".*\)/\1$dns_ip_name:$select_port\2/g" Config.xml
sed -i "s/\(.*httpServiceUrl value=\"http:\/\/\).*\(\/root.*\)/\1$dns_name\2/g" Config.xml

#使用sed修改nginx配置,重启
rm -f nginx_template.conf
download "common/nginx_template.conf"
sed -i "/^\s*server_name\s/c\\\t\\tserver_name ${dns_name};" nginx_template.conf
sed -i "/^\s*root\s/c\\\t\\troot /app/${Main_server}/www_${server_flag}/;" nginx_template.conf
sed -i "/^\s*access_log\s/c\\\t\\taccess_log  logs/${server_flag}.access.log  main;" nginx_template.conf
sed -i "/^\s*proxy_pass\s/c\\\t\\t\\tproxy_pass http://127.0.0.1:${http_port}/root/;" nginx_template.conf
sed -i "/^\s*proxy_set_header\sX-Real-Server/c\\\t\\t\\tproxy_set_header X-Real-Server ${server_lys};" nginx_template.conf
mv nginx_template.conf /app/nginx/conf/vhost/${game}_${server_flag}.conf
sudo /app/nginx/sbin/nginx -t 2>&1|grep "/app/nginx/conf/nginx.conf test is successful"
if [ $? -eq 0 ];then
    sudo /sbin/service nginx restart
    if [ $? -eq 0 ];then
        echo "restart nginx succ"
    else
        echo "ERROR: nginx error,restart nginx Fail"
    fi
else
    echo "ERROR: nginx error,nginx config error,please check!"
fi

#修改游戏中的配置
download "properties/${server_lys}.properties"
mv ${server_lys}.properties /app/$Main_server/backend/apps

####################################### 通用部分结束 ###############################################################################
cd /app/$Main_server/backend/apps
#....................修改跨服国战显示标志...........................
cname=`grep "gcld.showservername" $server_lys.properties |sed -e "s/gcld.showservername = //g;s/ *$/$server_id/g"`
server_cname=$(echo $cname|sed -e 's/\\/\\\\/g')
sed -i "s/\(gcld.serverchinesename = .*\)/\1-$server_cname/g" server.properties
sed -i "s/\(gcld.game.url = \).*/\1http:\/\/$dns_name/g" ${server_lys}.properties
sed -i "s/\(gcld.servername = \).*/\1${server_lys}/g" ${server_lys}.properties
sed -i "s/\(gcld.serverid = \).*/\1$server_id/g" ${server_lys}.properties
sed -i "s/\(gcld.serverids = \).*/\1S$server_id/g" ${server_lys}.properties
#修改运营商标示
sed -i "s/\(gcld.yx = .*\)/\1,${server_lys}/g" server.properties

#gameserver
sudo -u agent sed -i "/\[${server_lys}_S${server_id}\]/d" /app/${game}_backstage/socket_gameserver.ini
sudo -u agent echo "TOMCAT_PATH[${server_lys}_S${server_id}]=/app/${Main_server}/backend/">> /app/${game}_backstage/socket_gameserver.ini
sudo -u agent sh /app/${game}_backstage/start.sh restart
ps x -A -o stime,cmd |grep socket_gameserver|grep -v grep
#启动游戏
if [ "$app_restart" == "yes" ];then
    > /app/$Main_server/backend/logs/start.out
    sh /app/$Main_server/backend/bin/startup.sh restart
    sleep 30
    for((i=1;i<=2;i++))
    do
       grep "Init Servlet Success in" /app/$Main_server/backend/logs/start.out
       if [ $? -eq 0 ];then
           break
       else
           sleep 5
       fi
    done
fi
