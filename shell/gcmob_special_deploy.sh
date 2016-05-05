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

cd /app/${Main_server}/backend/apps/
#应用汇充值。
if [ "$game" == "gcmob" -a "$server_lys" == "appchina" ];then
    sed -i "/^gcld.pay.url =/c\gcld.pay.url = http://${dnsname}/root/yxAppChinaPay.action" ${server_lys}.properties
fi
#快用的svr默认设置为空，否则要设置成联运商提供的值
if [ "$game" == "gcmob" -a "$server_lys" == "kuaiyong" ];then
    sed -i "s/\(gcld.kuaiyong.game.svr = \).*/\1/g" ${server_lys}.properties
fi
mainservername=$(echo $Main_server|cut -d'_' -f2,3)
#如果为主服，则修改跨服显示
if [ "$mainservername" == "$server_flag" ];then
    #跨服显示
    if [ "${server_lys}" == "feiliu" ];then
        sed -i "s/gcld.serverchinesename = .*/gcld.serverchinesename = \\\u653b\\\u57ce\\\u63a0\\\u5730${server_id}\\\u670d/g" server.properties
    elif [ "${server_lys}" == "feiliuapp" ];then
        sed -i "s/gcld.serverchinesename = .*/gcld.serverchinesename = \\\u653b\\\u57ce\\\u82f9\\\u679c${server_id}\\\u670d/g" server.properties
    elif [ "${server_lys}" == "yulong" ];then
        sed -i "s/gcld.serverchinesename = .*/gcld.serverchinesename = \\\u653b\\\u57ce\\\u817e\\\u8baf${server_id}\\\u670d/g" server.properties
    elif [ "${server_lys}" == "ilovemg" ];then
        sed -i "s/gcld.serverchinesename = .*/gcld.serverchinesename = S${server_id}\\\uc11c\\\ubc84/g" server.properties
    else
        sed -i "s/gcld.serverchinesename = .*/gcld.serverchinesename = ${server_lys}${server_id}/g" server.properties
    fi
fi
