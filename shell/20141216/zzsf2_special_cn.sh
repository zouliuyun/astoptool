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
########
backend_dir=/app/$Main_server/backend/apps
www_dir=/app/$Main_server/www_${server_flag}
if [ "$server_lys" == "renren" ];then
    Main=index.html
    dnsname_renren="x${server_id}.zzsf2.renren.com"
    sed -i "s/s1.zzsf2.renren.com/$dns_name/g" $www_dir/index.html
    sed -i "s/x1.zzsf2.renren.com/$dnsname_renren/g" $www_dir/Main.html
    sed -i "s/s1.zzsf2.renren.com/$dns_name/g" $backend_dir/${server_lys}.properties
elif [ "$server_lys" == "kuaiwan" ];then
    if [ "$server_id" -lt 10 ];then
        sed -i "s/game_id=8505001/game_id=850500${server_id}/g" $backend_dir/${server_lys}.properties
    elif [ "$server_id" -lt 100 ];then
        sed -i "s/game_id=8505001/game_id=85050${server_id}/g" $backend_dir/${server_lys}.properties
    elif [ "$server_id" -lt 1000 ];then
        sed -i "s/game_id=8505001/game_id=8505${server_id}/g" $backend_dir/${server_lys}.properties
    fi
elif [ "$server_lys" == "pps" ];then
    if [ "$server_id" -lt 10 ];then
        sed -i "s/server_type=194001/server_type=19400${server_id}/g" $backend_dir/${server_lys}.properties
    elif [ "$server_id" -lt 100 ];then
        sed -i "s/server_type=194001/server_type=1940${server_id}/g" $backend_dir/${server_lys}.properties
    elif [ "$server_id" -lt 1000 ];then
        sed -i "s/server_type=194001/server_type=194${server_id}/g" $backend_dir/${server_lys}.properties
    fi
fi
#if [ "$server_name" == "pptv" ];then
#    sed -i "s/\(zzsf2.pay.url.*sid=\).*/\1${server_id}/g" $backend_dir/${server_lys}.properties
#fi
#修改首服的java内存
if [ "$server_id" -eq 1 ];then
    sed -i s/2000m/3000m/g /app/$Main_server/backend/bin/catalina.sh
fi
