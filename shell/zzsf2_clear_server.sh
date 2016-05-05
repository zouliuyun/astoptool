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

clear_script=make_truncate_db.sh
email_address="yanghj@game-reign.com,sunhao@game-reign.com,lixl@game-reign.com,liuyi@game-reign.com,wufan@game-reign.com"
#email_address="zouly@game-reign.com"
email_caddress="opteam@game-reign.com"

function send_mail()
{
    sendEmail -s mail.game-reign.com -f clearinfo@game-reign.com -t $email_address -cc $email_caddress -u "[$1][$game][${servername}][online:${online_number}][clear result][$(date +'%Y-%m-%d %H:%M:%S')]" -m "$2"  -o message-charset=utf8 
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
rm -rf /app/${server_tag}/backend/logs/*
rm -rf /app/${server_tag}/backend/fight/*
rm -rf /app/${server_tag}/backend/temp/*
mkdir -p /app/opbak/dbbak
cd /app/opbak/dbbak/
online_number=`pandora ${server_tag} -e 'select count(1) from player where player_lv >=10;'| sed "1d;"`
if [ "$online_number" -ge 10 ];then
    echo "${server_tag} lv >=10 players great than 10"
    sendEmail -s mail.game-reign.com -f zabbix@game-reign.com -t $email_address -u "${server_tag} clear_db" -m "More than 10 players and player_lv >=10 ($online_number players) when clear db ${server_tag},please know!"
fi
pandora --dump --opt -R ${server_tag} > ${server_tag}_`date +%Y%m%d%H%M`.sql
cd /app/${server_tag}
rm -f ${clear_script} &>/dev/null
download  "clear/${clear_script}"
#执行生成清档脚本
rm -f truncate_db.sql &>/dev/null
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
#活动配置
cd /app/${server_tag}
rm system.activity
download  "clear/system.activity"
activity=`cat system.activity|sort|uniq |tail -n 1`
sed -i "/^system.activity/d" /app/${server_tag}/backend/apps/server.properties
sed -i "/统预设活动/a$activity" /app/${server_tag}/backend/apps/server.properties
rm system.activity
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
###############check###########################################################
domain=`cat /app/${server_tag}/backend/apps/${yx}.properties | grep -E "^([a-z0-9]*\.)?game.url" |sed -r -e "s/^([a-z0-9]*.)?game.url.*= *//g;s/http:\/\///"`
url=`cat /app/${server_tag}/backend/apps/${yx}.properties | grep -E "^([a-z0-9]*\.)?game.url" |sed -r -e "s/^([a-z0-9]*.)?game.url.*= *//g;s/$/\/root\/gateway.action?command=version/g;"`
update_back_version=`curl -s "${url}"  2>/dev/null |sed 's/.*zzsf2"://g;s/\,.*//g;s/\"//g'`
if [ -z $update_back_version ];then
    send_mail "fail" "start ${server_tag} fail"
else
    TIME_start=`ps x -o stime,cmd|grep "java.*\<${server_tag}\>.*backend" |grep -v grep|awk '{print $1}'`
    GAME_init_time=`/usr/bin/pandora ${server_tag} -e 'select FROM_UNIXTIME(ceil(property_value/1000)) as starttime from server_state where property_name="zzsf2.server.time";'|grep -v starttime`
    dbversion=`/usr/bin/pandora ${server_tag} -e 'select db_version from db_version'|grep -v db_version`
    mail_html=/app/opbak/${server_tag}_clear.html
    echo "<td>Dear QA&运营</td></br>" >$mail_html
    echo "<td>  [<span style='color:blue'>${server_tag}</span>]清档完成，请QA和运营测试</td></br>" >>$mail_html
    echo "<td> <span style='color:blue'>===清档后常规信息如下===</span></td></br>" >>$mail_html
    echo "<td>  游戏进程重启时间:<span style='color:blue'>`date +%Y-%m-%d` ${TIME_start}</span></td></br>" >>$mail_html
    echo "<td>  游戏内初始时间:<span style='color:blue'>$GAME_init_time</span></td></br>" >>$mail_html
    echo "<td>  数据库版本:<span style='color:blue'>$dbversion</span></td></br>" >>$mail_html
    echo "<td>  后端版本:<span style='color:blue'>$update_back_version</span></td></br>" >>$mail_html
    grep -E "^([a-z0-9]*\.)?pay.url" /app/${server_tag}/backend/apps/${yx}.properties|grep -w "${domain}"
    if [ $? -eq 0 ];then
         echo "<td>  充值是否开启:<span style='color:blue'>否</span></td></br>" >>$mail_html
    else
         echo "<td>  充值是否开启:<span style='color:blue'>是</span></td></br>" >>$mail_html
         grep -E "^([a-z0-9]*\.)?pay.url" /app/${server_tag}/backend/apps/${yx}.properties |sed "s/$/\<\/br\>/">>$mail_html
    fi
    echo "<td> <span style='color:blue'>===新服活动配置信息如下===</span></td></br>" >>$mail_html
    grep "^system.activity" /app/${server_tag}/backend/apps/server.properties &>/dev/null
    if [ $? -ne 0 ];then
         echo "<span style='color:blue'>活动未开启</span></td></br>" >>$mail_html
    else
         grep "^system.activity" /app/${server_tag}/backend/apps/server.properties |sed "s/$/\<\/br\>/">>$mail_html
    fi
    echo "<td> <span style='color:blue'>===游戏配置检测结果如下、忽略联运配置多少错误===</span></td></br>" >>$mail_html
        cd /app/${server_tag}
        rm apps_check.tgz apps_check -rf &>/dev/null
        download  "clear/apps_check.tgz"
        tar -xzf apps_check.tgz
        cd apps_check
        python diff.py ${server_tag} |sed "s/$/\<\/br\>/">> $mail_html
        echo "</br>" >>$mail_html
        cd /app/${server_tag}
        echo "<td> <span style='color:blue'>===数据库结构检测结果如下===</span></td></br>" >>$mail_html
        /usr/bin/pandora --dump --opt -R -d ${server_tag} > ${server_tag}.check.sql
        version=`/usr/bin/pandora ${server_tag} -e 'select db_version from db_version' |grep  [0-9]` && echo "insert into db_version(db_version) values('$version');"   >> ${server_tag}.check.sql
        if [ $? -eq 0 ];then            
            rm table.py zzsf2_cn_init.sql &>/dev/null
            download  "clear/table.py"
            download  "common/zzsf2_cn_init.sql" 
            python table.py zzsf2_cn_init.sql new
            python table.py ${server_tag}.check.sql check >>$mail_html
        fi
        cd   /app/${server_tag} && rm table.py zzsf2_cn_init.sql ${server_tag}.check.sql zzsf2_check.sql   apps_check.tgz apps_check -rf
    sendEmail -f clearinfo@game-reign.com -t $email_address -cc $email_caddress  -u "[$game][${server_tag}][清档结果][`date +"%F %k:%M"`]" -o message-charset=UTF-8 -o message-content-type=html -o message-file=$mail_html
fi
###############################################################################
