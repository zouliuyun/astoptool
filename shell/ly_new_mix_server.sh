#!/bin/bash
export JAVA_HOME=/usr/local/jdk;
export LC_ALL="en_US.UTF-8";
export LANG="en_US.UTF-8";
sh /home/astd/.bash_profile
#配置
#中控地址
game=$1
download_ip=$2 #资源下载ip
download_url=$3 #资源下载的header
title=$4
server_flag=$5
dns_name=$6
Main_server=$7
dns_ip_name=$8 #Config.xml中配置游戏地址，如果为单ip则直接使用ip，如果是多ip则使用游戏域名
####################################################################################################################################
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

#拉取中控游戏模板文件地址
#template_propertiefile="${center_path}/template/properties/${server_lys}.properties"
#template_wwwfile="${center_path}/template/www_${server_lys}.tgz"
#创建游戏目录解压相应文件
cd /app/$Main_server/
#创建前端目录
download "template/www_${server_lys}.tgz"
tar -zxf ${server_lys}.tgz
if [ ! -d www_${server_name}_1 ];then
    echo "download  www_${server_name}.tgz fail !"
    exit 1;
elif [ "www_${server_name}_1" != "www_${server_flag}" ];then
    mv www_${server_name}_1 www_${server_flag}
fi
rm -f ${server_lys}.tgz


#修改游戏中的配置
cd /app/$Main_server/backend/apps
if [ -f ${server_lys}.properties ];then
    echo "${server_lys}.properties already exsist"
else
    download "template/properties/${server_lys}.properties"
fi

####################################### 通用部分结束 ###############################################################################
####################################### 以下为不同项目需要设置不同的东西 #################################

#....................修改跨服国战显示标志...........................
cname=`grep "${game}.showservername" $server_lys.properties |sed -e "s/${game}.showservername = //g;s/ *$/$server_id/g"`
server_cname=$(echo $cname|sed -e 's/\\/\\\\/g')
sed -i "s/\(${game}.serverchinesename = .*\)/\1-$server_cname/g" server.properties
#特殊联运renren，kaixin，xunlei
#其他的
sed -i "s/\(${game}.game.url = \).*/\1http:\/\/$dns_name/g" /app/${Main_server}/backend/apps/${server_lys}.properties
sed -i "s/\(${game}.servername = \).*/\1${server_lys}/g" /app/${Main_server}/backend/apps/${server_lys}.properties
sed -i "s/\(${game}.serverid = \).*/\1$server_id/g" /app/${Main_server}/backend/apps/${server_lys}.properties
sed -i "s/\(${game}.serverids = \).*/\1S$server_id/g" /app/${Main_server}/backend/apps/${server_lys}.properties

#联运商文件一些id的特殊配置     gcld:kuaiwan,ww,wyx,taobao

#修改运营商标示
sed -i "s/\(${game}.yx = .*\)/\1,${server_lys}/g" /app/${Main_server}/backend/apps/server.properties
#写入配置文件MD5值
#ls *.*| grep -v "md5.txt\|serverstate.properties\|CityInfo.xml\|WorldRoad.xml\|bak" |xargs md5sum  > md5.txt
#修改游戏主页标题
cd /app/${Main_server}/www_${server_flag}
if [ -z "$title" ];then
    echo "NO server title argements!"
else
    sed -i "s/\(<title>\).*\(<\/title>\)/\1 $title \2/g" /app/$Main_server/www_${server_flag}/Main.html
#版本特殊项
    #攻城:sed  -i "/isNewWorld/s/false/true/g" Config.xml
fi
sed -i "s/\(.*socketServiceUrl value=\"\).*\(\".*\)/\1$dns_ip_name:$select_port\2/g" /app/$Main_server/www_${server_flag}/Config.xml
sed -i "s/\(.*httpServiceUrl value=\"http:\/\/\).*\(\/root.*\)/\1$dns_name\2/g" /app/${Main_server}/www_${server_flag}/Config.xml

########临时修改前端版本
#sed -i "s/gcld_3-6-2/gcld_3-6-4/g" Main.html
#ls *.*| grep -v "md5.txt\|bak" |xargs md5sum  > md5.txt

####################################################################################################################################

#使用sed修改nginx配置,重启
download common/nginx_template.conf
if [ -f /app/nginx/conf/vhost/${servername}.conf ];then
    echo "/app/nginx/conf/vhost/${servername}.conf已经存在"
    exit 1
fi
sed -i "/^\s*server_name\s/c\\\t\\tserver_name ${dns_name};" nginx_template.conf
sed -i "/^\s*root\s/c\\\t\\troot /app/${Main_server}/www_${server_flag}/;" nginx_template.conf
sed -i "/^\s*access_log\s/c\\\t\\taccess_log  logs/${server_flag}.access.log  main;" nginx_template.conf
sed -i "/^\s*proxy_pass\s/c\\\t\\t\\tproxy_pass http://127.0.0.1:${http_port}/root/;" nginx_template.conf
sed -i "/^\s*proxy_set_header\sX-Real-Server/c\\\t\\t\\tproxy_set_header X-Real-Server ${server_lys};" nginx_template.conf
mv nginx_template.conf /app/nginx/conf/vhost/${servername}.conf
sudo /app/nginx/sbin/nginx -t 2>&1|grep "/app/nginx/conf/nginx.conf test is successful"
if [ $? -eq 0 ];then
    sudo /sbin/service nginx restart
    if [ $? -eq 0 ];then
        echo "restart nginx succ"
    else
        echo "nginx error,restart nginx Fail"
    fi
else
    echo "nginx error,nginx config error,please check!"
fi

#修改攻城掠地后端配置文件并重启gameserver
sudo -u agent sed -i "/\[${server_lys}_S${server_id}\]/d" /app/${game}_backstage/socket_gameserver.ini
sudo -u agent echo "TOMCAT_PATH[${server_lys}_S${server_id}]=/app/${Main_server}/backend/">> /app/${game}_backstage/socket_gameserver.ini
sudo -u agent sh /app/${game}_backstage/start.sh restart
ps x -A -o stime,cmd |grep socket_gameserver|grep -v grep
#启动游戏
 > /app/$Main_server/backend/logs/start.out
sh /app/$Main_server/backend/bin/startup.sh restart
sleep 30
for((i=1;i<=30;i++))
     do
        grep "Init Servlet Success in" /app/$Main_server/backend/logs/start.out
        if [ $? -eq 0 ];then
            break
        else
            sleep 5
        fi
done
