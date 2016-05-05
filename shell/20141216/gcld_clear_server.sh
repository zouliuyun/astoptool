#!/bin/bash
export JAVA_HOME=/usr/local/jdk;
export LC_ALL="en_US.UTF-8";
export LANG="en_US.UTF-8";

. /home/astd/.bash_profile
game=$1
servername=$2
yx=$(echo $servername|cut -d'_' -f1)
language=$3
server_tag=${game}_$servername
download_ip=$4
download_port=$5
download_header=$6

clear_script=truncate_db.sh

function send_mail()
{
    sendEmail -f clearinfo@game-reign.com -t opteam@game-reign.com -u "[$1][${server_tag}][clear result][$(date +'%Y-%m-%d %H:%M:%S')]" -m "$2"  -o message-charset=utf8
}
#参数：1、文件路径
function download()
{
   wget -c -t 2 -q --header="host:$download_header"  http://${download_ip}:${download_port}/$game/newserver/${language}/${1}
   if [ $? -ne 0 ];then
       echo "download ${1} failed!"
       send_mail "failed" "download ${1} failed!"
       exit 1
   fi
}

if [ -d /app/${server_tag}/ ];
then
    echo "Start clear $server_tag";
else
    echo "server $server_tag not exists";
    send_mail "failed" "server $server_tag not exists"
    exit 1
fi
sleep $(($RANDOM%30))
ps x |grep "/usr/local/jdk/bin/java.*/app/${server_tag}/backend"|grep -v grep | awk '{print $1}' |xargs kill -9
cd /app/${server_tag}/backend/apps/
rm -f serverstate.properties.bak && cp serverstate.properties{,.bak}
echo -e "gcld.nation.leagueInfo=0
gcld.open.league.wu=0
gcld.open.league.shu=0
gcld.open.league.wei=0" > serverstate.properties
rm -rf /app/${server_tag}/backend/logs/*
rm -rf /app/${server_tag}/backend/fight/*
rm -rf /app/${server_tag}/backend/temp/*
mkdir -p /app/opbak/dbbak
cd /app/opbak/dbbak/
pandora --dump --opt -R ${server_tag} > ${server_tag}_`date +%Y%m%d%H%M`.sql
cd /app/${server_tag}
rm -f ${clear_script}
download  "clear/${clear_script}"
#执行生成清档脚本
rm -f truncate_db.sql
sh ${clear_script} ${server_tag}
if [ $? -ne 0 ];then
	echo "生成清档脚本失败！"
	exit 1
fi
rm ${clear_script}
pandora --update ${server_tag} < truncate_db.sql
if [ $? == 0   ];then
    rm -f ${clear_script}
    rm -f truncate_db.sql
    cd /app/${server_tag}/backend
    sh bin/startup.sh restart
else 
    echo "导入清档脚本异常！很遗憾，清档失败了！"
    send_mail "failed" "import ${clear_script} failed!"
    exit 1
fi
#由于清档后日志丢失需重启logcheck
killall logcheck
send_mail "succ" "clear ${server_tag} succ"
