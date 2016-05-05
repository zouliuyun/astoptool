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
host_id=$(echo "$dnsname"|sed 's/.app1103834139.qqopenapp.com//g;s/s//g')
sed -i "s/\(gcld.host.id = \).*/\1$host_id/g" /app/$Main_server/backend/apps/${server_lys}.properties
