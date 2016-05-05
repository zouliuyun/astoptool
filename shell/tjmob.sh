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

echo '开始执行特殊配置脚本...'
echo "server_lys=${server_lys},server_id=${server_id}"
if [[ ${server_lys} = appstore ]]; then
    sed -i "/^gcld.game.url *=/c gcld.game.url = http:\/\/s${server_id}.tjapp.aoshitang.com\/" /app/${Main_server}/backend/apps/appstore.properties

    if [[ -f /app/nginx/conf/vhost/${Main_server}.conf ]]; then
        sed -i "s/\(s${server_id}.tjmob.aoshitang.com\)/\1 s${server_id}.tjapp.aoshitang.com/" /app/nginx/conf/vhost/${Main_server}.conf
        sudo /app/nginx/sbin/nginx -t
        sudo /app/nginx/sbin/nginx -s reload
    else
        exit 1
    fi
fi


cd /app/${Main_server}/backend/apps/
#命名区分开了，100服之后又重新从100开始算起
fake_id=$(expr ${server_id} - 100)
sed -i "/^gcld.showservername *=/c gcld.showservername = \\\u8D6B\\\u62C9\\\u7279" ${server_lys}.properties
sed -i "/^gcld.serverid.just.show *=/c gcld.serverid.just.show = ${fake_id}" ${server_lys}.properties
if [[ ${server_lys} = 37wan ]]; then
    echo 'Change gcld.serverchinesename in server.properties...'
    sed -i "/^gcld.serverchinesename *=/c gcld.serverchinesename = \\\u8D6B\\\u62C9\\\u7279${fake_id}" server.properties
fi





#为懒惰的运营写的开服活动定时设置
#function add_cron() {
#    new_cron=$1
#    crontab -l | { cat; echo '"${new_cron}"'; } | crontab -
#}
#
#if [[ ${game}_${server_flag} = ${Main_server} ]]; then
#    echo "insert into activity VALUE(4,date_add(curdate(), interval 6 day),date_add(curdate(), interval 7 day),'', '洗练活动');" >> $sqlfile
#    echo "insert into activity VALUE(2,date_add(curdate(), interval 7 day),date_add(curdate(), interval 8 day),'', '冲值返金币');" >> $sqlfile
#    echo "insert into activity VALUE(1,date_add(curdate(), interval 8 day),date_add(curdate(), interval 10 day),'', '国战经验加成');" >> $sqlfile
#    echo "insert into activity VALUE(8,date_add(curdate(), interval 9 day),date_add(curdate(), interval 10 day),'100,20,1;200,30,2;500,60,2;1000,70,2;2000,80,2', '打资源副本，送推恩令');" >> $sqlfile
#    echo "insert into activity VALUE(13,date_add(curdate(), interval 10 day),date_add(curdate(), interval 11 day),'', '镔铁征收活动');" >> $sqlfile
#
#


#if echo $Main_server | grep -q "tjmob_appstore_"; then
#    cp /app/${Main_server}/backend/apps/appstore.properties /app/${Main_server}/backend/apps/37wan.properties
#    sed -i '/^gcld.servername =/s/=.*/= 37wan/' /app/${Main_server}/backend/apps/37wan.properties
#    sed -i '/^gcld.yx =/s/=.*/= 37wan/' /app/${Main_server}/backend/apps/server.properties
#
#    export JAVA_HOME=/usr/local/jdk;
#    export LC_ALL="en_US.UTF-8";
#    export LANG="en_US.UTF-8";
#
#    . /home/astd/.bash_profile
#
#    /app/${Main_server}/backend/bin/start.sh restart
#
#    echo "TOMCAT_PATH[37wan_S10000${server_id}]=/app/tjmob_appstore_${server_id}/backend/" >>/app/tjmob_backstage/socket_gameserver.ini
#    cd /app/tjmob_backage && sudo -u agent sh start.sh restart
#    echo "RECONFIG FOR APPSTORE GAMESERVER"
#
#fi

#echo "sed -i \"/^gcld.mobile.server.showname =/s/= .*/= S${server_id}/\" /app/${Main_server}/backend/apps/${server_lys}.properties"

#sed -i "/^gcld.mobile.server.showname =/s/= .*/= S${server_id}/" /app/${Main_server}/backend/apps/${server_lys}.properties
