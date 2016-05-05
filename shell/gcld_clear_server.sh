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
#email_flag=$7

clear_script=truncate_db.sh

function send_mail()
{
    sendEmail -s mail.game-reign.com -f clearinfo@game-reign.com -t opteam@game-reign.com -u "[$1][$game][${servername}][online:${online_number}][clear result][$(date +'%Y-%m-%d %H:%M:%S')]" -m "$2"  -o message-charset=utf8
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
logBackDir="/app/opbak/clear/${server_tag}"
mkdir -p $logBackDir
cp -r /app/${server_tag}/backend/logs $logBackDir
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
if [ "$game" == "gcld" ];then
    email_address=ocgcld@game-reign.com,tech-op@game-reign.com,Global-Operate@game-reign.com
else
    email_address=tech-op@game-reign.com
fi
online_number=`pandora ${server_tag} -e 'select count(1) from player where player_lv >=10;'| sed "1d;"`
if [ "$online_number" -ge 10 ];then
    echo "${server_tag} lv >=10 players great than 10"
    sendEmail -s mail.game-reign.com -f zabbix@game-reign.com -t $email_address -u "${server_tag} clear_db" -m "More than 10 players and player_lv >=10 ($online_number players) when clear db ${server_tag},please know!"
fi
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
else 
    echo "导入清档脚本异常！很遗憾，清档失败了！"
    send_mail "failed" "import truncate_db.sql failed!"
    exit 1
fi
cd /app/${server_tag}/backend
sh bin/startup.sh restart
sleep 60
tcpport=$(grep 'property.*name="port"' /app/${server_tag}/backend/apps/conf.xml|cut -d'>' -f2|cut -d '<' -f1|grep -o [0-9]*)
if [ -n "$tcpport" ];then
    for ((i=1;i<40;i++))
    do
        netstat -ntl|grep -q "0.0.0.0:$tcpport "
        if [ $? -eq 0 ];then
            echo "server ${server_tag} start succ"
            break
        fi
        sleep 60
        if [ $(($i%10)) == 0 ];then
                sh bin/startup.sh restart
                echo "restart ${server_tag} at $(($i/10)) times"
        else
                echo "$i---go on grep log"
        fi
    done
fi
#由于清档后日志丢失需重启logcheck
#killall logcheck
logcheck_pid=`ps x |grep './logcheck'|grep -v grep|awk '{print $1}'`
if [ ! -z "$logcheck_pid" ];then
    kill -9 $logcheck_pid
fi
#海外特殊项目--删除定时任务
if [ "$game" ==  "nhmob" ];then
    day=`date +%d`
    month=`date +%m`
    crontab -l >/home/astd/.cron/astd_cron_${server_tag}
    sed -i "/$day $month \* sh \/app\/opbin\/nhmob\/allinone\/shell\/gcld_clear_server.sh '$game' '$servername' '$language'/d"  /home/astd/.cron/astd_cron_${server_tag}
    crontab /home/astd/.cron/astd_cron_${server_tag}
fi
#if [ "$email_flag" != "noemail" ];then
send_mail "succ" "clear ${server_tag} succ"
#fi
