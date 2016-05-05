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
wwwdir=www_${server_flag}

echo '开始执行特殊配置脚本...'
echo "server_lys=${server_lys},server_id=${server_id}"

if [ "$server_lys" == "kuaiwan" ];then
    if [ "$server_id" -lt 10 ];then
        sed -i "s/game_id=8505001/game_id=850500${server_id}/g" /app/${Main_server}/backend/apps/${server_lys}.properties
    elif [ "$server_id" -lt 100 ];then
        sed -i "s/game_id=8505001/game_id=85050${server_id}/g" /app/${Main_server}/backend/apps/${server_lys}.properties
    elif [ "$server_id" -lt 1000 ];then
        sed -i "s/game_id=8505001/game_id=8505${server_id}/g" /app/${Main_server}/backend/apps/${server_lys}.properties
    fi
fi
if [ "$server_lys" == "pps" ];then
    if [ "$server_id" -lt 10 ];then
        server_type=1845503
        sed -i "s/server_type=1845501/server_type=184550${server_id}/g" /app/${Main_server}/backend/apps/${server_lys}.properties
    elif [ "$server_id" -lt 100 ];then
        sed -i "s/server_type=1845501/server_type=18455${server_id}/g" /app/${Main_server}/backend/apps/${server_lys}.properties
    elif [ "$server_id" -lt 1000 ];then
        sed -i "s/server_type=1845501/server_type=1845${server_id}/g" /app/${Main_server}/backend/apps/${server_lys}.properties
    fi
fi
if [ "$server_flag" == "renren" ];then
    Main=index.html
    dnsname_renren="x${server_id}.zzsf2.renren.com"
    sed -i "s/s1.zzsf2.renren.com/$dns_name/g" /app/${Main_server}/$wwwdir/index.html
    #sed -i "s/x1.zzsf2.renren.com/$dnsname_renren/g" /app/${Main_server}/$wwwdir/Main.html
    sed -i "s/\(zzsf2.game.url = \).*/\1http:\/\/$dns_name\/Main.html/g" /app/${Main_server}/backend/apps/${server_flag}.properties
    sed -i "s/\(zzsf2.domain = \).*/\1http:\/\/$dns_name\/g" /app/${Main_server}/backend/apps/${server_flag}.properties
fi
