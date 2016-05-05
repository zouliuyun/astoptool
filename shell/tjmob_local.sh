#!/bin/bash
while getopts ":g:m:s:i:" optname
    do
        case "$optname" in
             "g")
              game="$OPTARG"
              ;;
             "m")
              Main_server="$OPTARG"
              ;;
             "s")
              mixserver_list="$OPTARG"
              ;;
             "i")
              w_ip="$OPTARG"
              ;;
        esac
done
SSH="ssh -o ConnectionAttempts=10 -o ConnectTimeout=5"

for mix_server in $(echo $mixserver_list|sed 's/,/ /g'); do
    server_lys=$(echo $mix_server|cut -d'_' -f1)
    server_id=$(echo $mix_server|cut -d'_' -f2)

    if [[ ${server_lys} = appstore ]]; then
        echo 'Adding dns for tjapp...'
        result=$($SSH astd@10.6.196.65 "/app/opbin/dns/dnsapi -g tjmob -a add -d s${server_id}.tjapp -l 1 -i ${w_ip}")
        echo $result
        if echo $result | grep -i 'success' >/dev/null; then
            exit 0
        else
            exit 1
        fi
    fi
done
