#!/bin/bash
games=$1
server_flag=$2
CONF_DIR="$(dirname $(readlink -f $0))/../conf"
WORK_HOME="$(dirname $(readlink -f $0))/.."
ssh_cmd="ssh -o ConnectionAttempts=10 -o ConnectTimeout=5"
MESSAGE=""
specialflag=0
flagspecial=0
errorflag=0

cd $WORK_HOME
test -d domain_list || mkdir domain_list
test -d domain_list/bak || mkdir domain_list/bak
test -f domain_list/bak/special.tmp || touch domain_list/bak/special.tmp
if [ -f domain_list/all_game_domain_newserver ];then
    cp ./domain_list/all_game_domain_newserver ./domain_list/bak/all_game_domain_newserver_bak
else
    touch ./domain_list/all_game_domain_newserver ./domain_list/bak/all_game_domain_newserver_bak
fi

cd $CONF_DIR
if [ -z "$games" ];then
games=`ls | grep -Ev "conf.tmp|logger.conf|main.conf" | sed 's/\(.*\)\.conf/\1/g'`
fi

okcount=1
for game in $games
do
    echo -e "\n###################################################################################"
    echo " game name is '$game' " 
    sed -i "/$game@$server_flag/d" ${WORK_HOME}/domain_list/bak/all_game_domain_newserver_bak
    big_mix_server=`grep "big_mix_server" $game.conf | cut -d ' ' -f3`
    subs=`grep '\[.*\]' $game.conf | grep -v "\[common\]" | sed 's/\[\(.*\)\]/\1/g'`
    class=($subs)
    sum=${#class[@]}
    i=0
    endnum=$(($sum-1))
    echo -e "this project big_mix_server=${big_mix_server} , have class iteams :\n[$subs] "
    if [ $sum -ne 0 ];then

        for sub in $subs
        do
            echo -e "### now class iteam is [$sub] begin ;;\n"
            if [ $i -eq $endnum ];then
                awk "/\[${class[$i]}\]/,0" $game.conf > conf.tmp
            else
                j=$(($i+1))
                awk "/\[${class[$i]}\]/,/\[${class[$j]}\]/" $game.conf > conf.tmp
            fi
            backstage=`cat conf.tmp | grep "\<backstage\>" | cut -d ' ' -f3`
            backstage_db=`cat conf.tmp | grep "\<backstage_db\>" | cut -d ' ' -f3`
            is_oversea=`cat conf.tmp | grep "\<is_oversea\>" | cut -d ' ' -f3`
            language=`cat conf.tmp | grep "\<backstage_tag\>" | cut -d ' ' -f3`
            source_domain=`cat conf.tmp | grep "\<source_domain\>" | cut -d ' ' -f3`
            
            if [ -z "$server_flag" ];then
                if [ "$is_oversea" == "1" ];then
                    sqlstr='select concat(server.server_flag,\"_\",server.name),server.server_name, server.n_ip,web_url from server join partners on server.server_flag=partners.flag where type=2 and server.status&1=1 and server.istest=0 and server.mixflag=1 and partners.name like \"'${language}'%\" and partners.type=2 and partners.status=1 group by server.server_flag;' 
                    servers=`$ssh_cmd astd@$backstage "pandora $backstage_db -e \"$sqlstr\"" |grep -v 'concat(server.server_flag'|sed 's/\t/@/g;s/_S/_/g;s#http://##g;s#/root.*##g'`
                else
                    servers=`$ssh_cmd astd@$backstage "pandora $backstage_db -e \"select concat(server_flag,'_',name),server_name,n_ip,web_url from server where status&1=1 and istest=0 group by server_flag;\""|grep -v 'concat(server_flag'|sed 's/\t/@/g;s/_S/_/g;s#http://##g;s#/root.*##g'`
                fi
            else
                servers=`$ssh_cmd astd@$backstage "pandora $backstage_db -e \"select concat(server_flag,'_',name),server_name,n_ip,web_url from server where server_flag='$server_flag' and status&1=1 and istest=0 group by server_flag;\""|grep -v 'concat(server_flag'|sed 's/\t/@/g;s/_S/_/g;s#http://##g;s#/root.*##g'`
            fi

            for server in $servers
            do
#servername为该联运商服标识 tomcat为主服标识  如果不相等 则为混服
                servername=`echo $server|awk -F@ '{print $1}'`
                tomcat=`echo $server|awk -F@ '{print $2}'`
                serverip=`echo $server|awk -F@ '{print $3}'`
                serverurl=`echo $server|awk -F@ '{print $4}'`
                serverurl_ok=`echo $server|awk -F@ '{print $4}' | sed 's/^s[0-9]*\./s\${serverid}\./'`
                echo "${serverurl_ok}" | grep  '${serverid}' > /dev/null
                if [ "$?" != "0" ];then
                    specialflag=1
                    flagspecial=1
                fi

                if [ $is_oversea == "0" ];then
                servercname=$($ssh_cmd astd@gcld_gcld_1 "dig $serverurl | grep \"$source_domain\" | tail -1 " | awk '{print $1}' | sed 's/.aoshitang.com.$//g' | sed 's/^s[0-9]*\./s\${serverid}\./')
                echo "${servercname}" | grep  '${serverid}' > /dev/null   
                    if [ "$?" != "0" ];then
                        specialflag=1
                        flagspecial=1
                    fi
                else
                    servercname="oversea"
                fi

                if [ "$big_mix_server" == "1" ];then
                    if [ "$tomcat" == "$servername" ];then
                        title=$($ssh_cmd astd@$serverip "grep '<title>' /app/${game}_${tomcat}/www/Main.html"|sed 's/<title> *//g;s/ *<\/title>//g'|sed 's/1服/${serverid}服/g;s/1区/${serverid}区/g')
                    else
                        continue
                    fi
                else
#if [ "$tomcat" == "$servername" -a "$game" != "zzsf2" ];then  
#是否要校验混服?  zzsf2 特殊
                    if [ "$tomcat" == "$servername" ];then 
                        title=$($ssh_cmd astd@$serverip "grep '<title>' /app/${game}_${tomcat}/www/Main.html"|sed 's/<title> *//g;s/ *<\/title>//g'|sed 's/1服/${serverid}服/g;s/1区/${serverid}区/g')
                    else
                    title=$($ssh_cmd astd@$serverip "grep '<title>' /app/${game}_${tomcat}/www_${servername}/Main.html"|sed 's/<title> *//g;s/ *<\/title>//g'|sed 's/1服/${serverid}服/g;s/1区/${serverid}区/g')
                    fi
                fi
                
                if [ -z "$servercname" ];then
                    echo -e "\n[$okcount]---servercname error :"
                    grep "$game@$servername@" ${WORK_HOME}/domain_list/all_game_domain_newserver 
                    if [ "$?" == "0" ];then
                        grep "$game@$servername@" ${WORK_HOME}/domain_list/all_game_domain_newserver >> ${WORK_HOME}/domain_list/bak/all_game_domain_newserver_bak
                    else
                        specialflag=1
                        errorflag=1
                        echo "..........don't have servercname , serverurl: $serverurl"
                        echo "..........this server '$game' iteam '$sub' info >> special.tmp"
                        MESSAGE="$MESSAGE\n$game@$servername url:$serverurl will >> special.tmp"
                        servercname="Error-nohave-servercname"
                        title="Error-nohave-servercname"
                    fi
                    okcount=$((okcount+1))
                elif [ -z "$title" ];then
                    echo -e "\n[$okcount]---title error :"
                    grep "$game@$servername@" ${WORK_HOME}/domain_list/all_game_domain_newserver
                    if [ "$?" == "0" ];then
                        grep "$game@$servername@" ${WORK_HOME}/domain_list/all_game_domain_newserver >> ${WORK_HOME}/domain_list/bak/all_game_domain_newserver_bak
                    else
                        specialflag=1
                        errorflag=1
                        echo "..........don't have title"
                        echo "..........this server '$game' iteam '$sub' info >> special.tmp"
                        MESSAGE="$MESSAGE\n$game@$servername title:None will >> special.tmp"
                        title="Error-nohave-title"
                    fi
                    okcount=$((okcount+1))
                else
                    printf "[OK_$okcount]"
                    okcount=$((okcount+1))
                fi
                
                if [ "$specialflag" == "0" ];then
                    echo "$game@$servername@${serverurl_ok}@$servercname@$title" >> ${WORK_HOME}/domain_list/bak/all_game_domain_newserver_bak
                else
                    grep "$game@$servername@${serverurl_ok}@$servercname@$title" ${WORK_HOME}/domain_list/bak/special.tmp > /dev/null
                    if [ "$?" != "0" ];then
                        if [ "$flagspecial" == "1" -a "$errorflag" == "0" ];then
                            echo "#$game@$servername@${serverurl_ok}@$servercname@$title" >> ${WORK_HOME}/domain_list/bak/special.tmp
                        else
                            echo "$game@$servername@${serverurl_ok}@$servercname@$title" >> ${WORK_HOME}/domain_list/bak/special.tmp
                        fi
                    fi
                fi
                specialflag=0
                flagspecial=0
                errorflag=0
            done
            i=$(($i+1))
            echo -e "\n### [$sub] end ;;\n"
        done
    else
        echo "class is null , this project have no iteam !"
    fi
    echo -e " project game '$game' is over ######################################## \n"
done

echo -e "\n##############################all game end####################################\n"

abs() { echo ${1#-}; }
N_NOW=`cat ${WORK_HOME}/domain_list/bak/all_game_domain_newserver_bak|wc -l`
N_OLD=`cat ${WORK_HOME}/domain_list/all_game_domain_newserver|wc -l`
NUM=`abs $((N_NOW-N_OLD))`
DATE=`date +%Y%m%d%H%M%S`
if [ $NUM -gt 20 ];then
    echo "more than 20 items change ,maybe some thing is wrong,please check!"
    MESSAGE="$MESSAGE\n \n more than 20 items change,you'd better check it"
else
    cp ${WORK_HOME}/domain_list/all_game_domain_newserver ${WORK_HOME}/domain_list/bak/all_game_domain_newserver_${DATE}
    cat ${WORK_HOME}/domain_list/bak/all_game_domain_newserver_bak | sort -u > ${WORK_HOME}/domain_list/all_game_domain_newserver
fi
if [ ! -z "$MESSAGE" ];then
    sendEmail -f template-domain@game-reign.com -t liyang@game-reign.com -u "server_1 not resolve" -m "$(echo -e $MESSAGE|sed '/^$/d')"
fi
echo -e "\n this script will verify the file corrective and send mail to inform Administrator Error\n"
echo -e "\n this script update ${WORK_HOME}/domain_list/all_game_domain_newserver\n"
echo -e "\n this script update ${WORK_HOME}/domain_list/bak/special.tmp\n"
echo -e "\n this script update ${WORK_HOME}/domain_list/bak/all_game_domain_newserver_bak\n"
echo -e "\n this script create ${WORK_HOME}/domain_list/bak/all_game_domain_newserver_${DATE}"
