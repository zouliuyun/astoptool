#!/bin/bash
export JAVA_HOME=/usr/local/jdk;
export LC_ALL="en_US.UTF-8";
export LANG="en_US.UTF-8";
sh /home/astd/.bash_profile
####################################################################    变量    ####################################################
game=$1 #项目名称，gcld、gcmob
language=$2
server_flag=$3 #游戏名称,feiliu_1
title=$4    #html标题
dns_name=$5 #游戏域名
dns_ip_name=$6 #Config.xml中配置游戏地址，如果为单ip则直接使用ip，如果是多ip则使用游戏域名
apptype=$7 #应用类型，web、mobile
clear_time=$8 #清档时间
sqlfilename=$9 #游戏建库sql名称
old_www=${10}  #www是否还是老的模式{old,new}，老的格式为(主服名称为www，混服为www_lyx_id),新的格式为(www_lyx_id)
######下载相关信息
download_ip=${11} #资源下载ip
download_port=${12} #资源下载端口
download_url=${13} #资源下载的header
#清档脚本
clear_script=${14}
#打包的公共包
template_tar_dir=${15}
#日志、fight目录列表
template_exclude_dir=${16}

#################################
function exit_error()
{
    if [ $? -ne 0 ] ;then
        echo "Error: $1"
        exit 1
    fi
}
function download()
{
    wget -c -t 10 -T 10 -q --header=HOST:$download_url http://${download_ip}:${download_port}/$game/newserver/${language}/$1
    exit_error "下载${1}失败!"
}
#判断内存是否超出了上限
for i in $(grep "^JAVA_OPTS" /app/*/bin/catalina.sh /app/*/backend/bin/catalina.sh |awk -F'Xms' '{print $2}'|cut -d'm' -f1);do 
    usedMem=$((usedMem+i));
done;
mysqlMem=$(grep buffer_pool /etc/my.cnf | cut -d'=' -f2|xargs echo|sed 's/G/000/g')
usedMem=$((usedMem+mysqlMem))
totalMem=$(free -m|grep Mem|awk '{print $2}')
if [ x"$usedMem" != x"" -a $usedMem -gt $totalMem ];then
    echo "内存超出了物理内存，请确认"
    exit 1
fi
##############################初始化##############################################
wget_cmd="wget -c -t 10 -T 10 -q --header=HOST:$download_url"                   
#允许开放端口列表
if [ $apptype == "web" ];then 
    allowd_ports="9010 9020 9030 9040 9050 9060 9070 9080 9090 9100 9110 9120 9130 9140 9150 9160 9170 9180 9190 9200"
    #allowd_ports="9170 9180 9190 9200"
else
    allowd_ports="8210 8220 8230 8240 8250 8260 8270 8280 8290 8300 8310 8320 8330 8340 8350 8360 8370 8380 8390 8400"
fi
servername=${game}_${server_flag}
server_lys=`echo $server_flag |head -n 1 |cut -d '_' -f 1`
server_id=`echo $server_flag |head -n 1 |cut -d '_' -f 2`
month=`echo $clear_time |awk '{print $1}'|awk -F [-] '{print $2}'`
day=`echo $clear_time |awk '{print $1}'|awk -F [-] '{print $3}'`
hour=`echo $clear_time |awk '{print $2}'|awk -F [:] '{print $1}'`
minute=`echo $clear_time |awk '{print $2}'|awk -F [:] '{print $2}'`
cron_time="$minute $hour $day $month"
#替换配置  分配未使用的 端口
echo "Auto detect the free port:"
used_port_list=`grep -H 'port' /app/*/backend/apps/conf.xml |grep -v "/app/${servername}/" | sed -r 's/.*>([0-9]+).*$/\1/g'`   
select_port=""
#声明数组变量：is_port_used
declare -a is_port_used
for i in $allowd_ports;do
    is_port_used[$i]=0
done
for i in $used_port_list;do
    is_port_used[$i]=1
    echo -e "Port has been used:   $i"
done
#${!is_port_used[@]}，反查数组序号
for i in ${!is_port_used[@]};do
    if [ ${is_port_used[$i]} == 0 ];then
        select_port=$i
        break
    fi
done
if [ -z $select_port ];then
    echo "No more port for newserver"
    exit 1
else
    echo -e "Use port: $select_port"
fi
http_port=`expr $select_port + 1`
###################通用部分#################################################################################################################
#创建游戏目录解压相应文件
mkdir -p /app/${servername}/
cd /app/${servername}/

#创建后端目录
download "template/${server_lys}.tgz"
tar -zxf ${server_lys}.tgz
rm -f ${server_lys}.tgz
#下载公共的包{font,lib等等}
for i in $(echo $template_tar_dir|sed 's/,/ /g')
do
    if [ "$(echo $i)" == "" ];then
        continue
    fi
    i_path=$(dirname $i)
    i_filename=$(basename $i)
    cd /app/${servername}/$i_path
    download common/${i_filename}.tgz
    tar zxf ${i_filename}.tgz
    rm -f ${i_filename}.tgz
done
#创建必须目录{logs,fight等等}
for i in $(echo $template_exclude_dir|sed 's/,/ /g')
do
    if [ "$(echo $i)" == "" ];then
        continue
    fi
    i_path=$(dirname $i)
    i_filename=$(basename $i)
    cd /app/${servername}/$i_path
    mkdir -p ${i_filename}
done

#www设置
#if [ $apptype == "web" ];then
cd /app/${servername}/
wwwdir=""
if [ $old_www == "old" ];then
    mkdir www
    cd www
    wwwdir="www"
else
    mkdir www_${server_lys}_${server_id}
    cd www_${server_lys}_${server_id}
    wwwdir="www_${server_lys}_${server_id}"
fi
download "www/www_${server_lys}.tgz"
tar -zxf www_${server_lys}.tgz
rm -f www_${server_lys}.tgz
####################################### 通用部分结束 ##################################################
####################################### 以下为不同项目需要设置不同的东西 #################################
#修改游戏主页标题
if [ -z "$title" ];then
    echo "NO server title argements!"
else
    sed -i "s/\(<title>\).*\(<\/title>\)/\1 $title \2/g" Main.html
    test -f Main2.html && sed -i "s/\(<title>\).*\(<\/title>\)/\1 $title \2/g" Main2.html
fi
sed -i "s/\(.*socketServiceUrl value=\"\).*\(\".*\)/\1${dns_ip_name}:${select_port}\2/g" Config.xml
sed -i "s/\(.*httpServiceUrl value=\"https\?:\/\/\).*\(\/root.*\)/\1${dns_name}\2/g" Config.xml

#下载联运配置文件
cd /app/${servername}/backend/apps/
rm -f ${server_lys}.properties
download properties/${server_lys}.properties

#################################################################     修改配置     #################################################
#.修改跨服国战显示标志
cname=`grep -E "^([a-z0-9]*\.)?showservername" $server_lys.properties |sed -e "s/^([a-z0-9]*.)?showservername = //g;s/ *$/$server_id/g"`
server_cname=$(echo $cname|sed -e 's/\\/\\\\/g')
sed -i 's/\(^[a-z0-9]*\.\?serverchinesename = \).*/\1'$server_cname'/g' server.properties
#联运配置文件修改
sed -i "s/\(^[a-z0-9]*\.\?game.url = https\?:\/\/\)[^\/]*\(.*\)/\1${dns_name}\2/g" ${server_lys}.properties
sed -i "s/\(^[a-z0-9]*\.\?servername = \).*/\1${server_lys}/g" ${server_lys}.properties
sed -i "s/\(^[a-z0-9]*\.\?serverid = \).*/\1$server_id/g" ${server_lys}.properties
sed -i "s/\(^[a-z0-9]*\.\?serverids = \).*/\1S$server_id/g" ${server_lys}.properties
#修改http端口
sed -i "s/\(.*httpPort.*>\).*\(<.*\)/\1$http_port\2/g" conf.xml
#修改数据库名称
sed -i "s/\(.*jdbc.*127.0.0.1:3306\/${game}_\).*[0-9]<\(.*\)/\1${server_flag}<\2/g" applicationContext.xml
sed -i "s/\(.*127.0.0.1:3306\/${game}_\).*?\(.*\)/\1${server_flag}?\2/g" applicationContext.xml
#修改运营商标示
sed -i "s/\(^[a-z0-9]*\.\?yx = \).*/\1${server_lys}/g" server.properties
#修改战报路径
sed -i "s/\(^[a-z0-9]*\.\?report.linux.path.*app\).*[0-9]\(.*\)/\1\/${servername}\2/g" server.properties
#修改跨服战唯一标示key
sed -i "s/\(^[a-z0-9]*\.\?serverkey = \).*/\1${server_lys}_S${server_id}/g" server.properties
#修改后端端口
sed -i "s/\(.*port.*>\).*\(<.*\)/\1${select_port}\2/g" conf.xml
#初始化开服时间
if [ ! -f serverstate2.properties ];then
    download common/serverstate2.properties
fi
sed -i "/^[a-z0-9]*\.\?server.time=/d"  serverstate2.properties
cp serverstate2.properties serverstate.properties
###################################################################################################################################
#####################     导入数据库     配置,重启nginx     配置,重启java游戏     部署logcheck监控     执行定时清档     ###########
#创建游戏数据库并导入建库脚本
cd /app/${servername}
rm -f $sqlfilename
download common/$sqlfilename
pandora --update -e "create database ${servername}"
if [ $? -ne 0 ];then
    echo "create db fail!"
    exit 1
else
    echo "create db success"
fi
pandora --update ${servername} < $sqlfilename
if [ $? -ne 0 ];then
    echo "initial db fail!"
    exit 1
else
    rm -f $sqlfilename
fi
#重新加载nginx配置
download common/nginx_template.conf
if [ -f /app/nginx/conf/vhost/${servername}.conf ];then
    echo "/app/nginx/conf/vhost/${servername}.conf已经存在"
    exit 1
fi
sed -i "/^\s*server_name\s/c\\\t\\tserver_name ${dns_name};" nginx_template.conf
sed -i "/^\s*root\s/c\\\t\\troot /app/${servername}/${wwwdir}/;" nginx_template.conf
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
if [ ! -d /app/${game}_backstage ];then
    echo "ERROR :Need deploy ${game}_backstage by yourself"
    echo "ERROR: backstage添加失败，backstage不存在"
else
    sudo -u agent sed -i "/\[${server_lys}_S${server_id}\]/d" /app/${game}_backstage/socket_gameserver.ini
    sudo -u agent echo "TOMCAT_PATH[${server_lys}_S${server_id}]=/app/${servername}/backend/">> /app/${game}_backstage/socket_gameserver.ini
    sudo -u agent sh /app/${game}_backstage/start.sh restart
    ps x -A -o stime,cmd |grep socket_gameserver|grep -v grep
fi
#启动游戏
sh /app/${servername}/backend/bin/startup.sh start
sleep 30
for((i=1;i<=30;i++))
do
    grep "Init Servlet Success in" /app/${servername}/backend/logs/start.out
    if [ $? -eq 0 ];then
        break
    else
        sleep 5
    fi
done

#部署logcheck监控
echo "-----------------deploy logcheck-----------------------"
if [ -d /app/opbin/logcheck ];then
    cd /app/opbin/logcheck/conf/
    sh make_conf.sh
    killall logcheck
    sleep 5
    ps x -o stime,cmd|grep "./logcheck"|grep -v grep
else
    echo "logcheck添加失败，logcheck不存在"
fi
#执行定时清档设置
mkdir -p /app/opbin/${game}/allinone/shells/ 
mkdir -p /app/opbin/${game}/allinone/logs/
cronFile=deploy_cron_$(date +"%s")
crontab -l >/tmp/$cronFile
echo "$cron_time * sh /app/opbin/${game}/allinone/shell/${clear_script} '$game' '$server_flag' '$language' '$download_ip' '$download_port' '$download_url' &>/app/opbin/${game}/allinone/logs/clear_${server_flag}_info.log" >> /tmp/$cronFile
crontab /tmp/$cronFile
rm -f /tmp/$cronFile
crontab -l |grep $server_flag
