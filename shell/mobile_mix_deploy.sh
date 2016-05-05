#!/bin/bash
export JAVA_HOME=/usr/local/jdk;
export LC_ALL="en_US.UTF-8";
export LANG="en_US.UTF-8";
sh /home/astd/.bash_profile
#配置
#中控地址
exit_with_help()
{
    echo "Usage: $0 [options] server_flag
          Options:
            -l : 混服服务器名字，默认 \"uc_100,xiaomi_100\"
            -m : 主服务器域名，默认 \"gcmob_feiliu_100\"
        "
    exit 0
}
#默认参数
while getopts ":l:m:s:h:r:" optname
    do
        case "$optname" in
            "l")
                mixserver_list="$OPTARG"
                ;;
            "m")
                Main_server="$OPTARG"
                ;;
            "s")
                specialDeploy="$OPTARG"
                ;;
            "h")
		        exit_with_help
                ;;
	        "r")
		        Restart="$OPTARG"
		        ;;
            "?")
                echo "Unkown option $OPTARG"
                exit_with_help;
                ;;
        esac
    done

function exit_none()
{
	if [ "$(echo $1)" == "" ];then
		echo "ERROR: $2"
		exit 1
	fi
}
function exit_error()
{
	if [ $? -ne 0 ];then
		echo "ERROR: $1"
		exit 1
	fi
}
function error()
{
	echo "ERROR: $1"
	exit 1
}
exit_none "$mixserver_list" "mix server name must be given!mulut split with ',',EG:uc_100,xiaomi_100"
exit_none "$Main_server" "main server must be given! EG: feiliu_100"
exit_none "$Restart" "restart server or not must be given! EG: {true|false}"
GAME=$(echo $Main_server|cut -d'_' -f1)
dirName=$(dirname $0)

if [ ! -d /app/$Main_server/ ];then
    error "mix to Main server:$Main_server not exsist"
fi
if [ ! -e /app/$Main_server/${Main_server}_properties.zip ];then
	error "/app/$Main_server/${Main_server}_properties.zip not exists!"
fi

cd /app/$Main_server/ && unzip ${Main_server}_properties.zip
exit_error "unzip ${Main_server}_properties.zip failed!"

Main_server_yx=$(echo $Main_server|cut -d'_' -f2)
game_url=$(grep -E "^[0-9a-z]*\.?game.url" /app/$Main_server/backend/apps/${Main_server_yx}.properties|cut -d'=' -f2|xargs echo|cut -d'/' -f3)

for mix_server in $(echo $mixserver_list|sed 's/,/ /g')
do
	#修改游戏中的配置
	cd /app/$Main_server/backend/apps
	mix_server_yx=$(echo $mix_server|cut -d '_' -f1)
	mix_server_quhao=$(echo $mix_server|cut -d '_' -f2)
	if [ -f ${mix_server_yx}.properties ];then
	    error "${mix_server_yx}.properties already exsist"
	else
	    if [ ! -f /app/$Main_server/${Main_server}_properties/${mix_server_yx}.properties ];then
		    error "ERROR: /app/$Main_server/${Main_server}_properties/${mix_server_yx}.properties not exists!"
	    else
	        mv /app/$Main_server/${Main_server}_properties/${mix_server_yx}.properties .
	    fi
	fi
	
	sed -i "s/\(^[a-z0-9]*\.\?game.url = https\?:\/\/\)[^\/]*\(.*\)/\1${game_url}\2/g" ${mix_server_yx}.properties
	sed -i "s/\(^[0-9a-z]*\.\?serverid = \).*/\1${mix_server_quhao}/g" ${mix_server_yx}.properties
	sed -i "s/\(^[0-9a-z]*\.\?serverids = \).*/\1S${mix_server_quhao}/g" ${mix_server_yx}.properties
	sed -i "s/\(^[0-9a-z]*\.\?kuaiyong.game.svr = \).*/\1${mix_server_quhao}/g" ${mix_server_yx}.properties
	sed -i "s/\(^[0-9a-z]*\.\?use.gm.commond = \).*/\10/g" ${mix_server_yx}.properties

	#修改运营商标示
	sed -i "s/\(^[0-9a-z]*\.\?yx = .*\)/\1,${mix_server_yx}/g" /app/${Main_server}/backend/apps/server.properties
    #特殊脚本修改
    if [ "$(echo $specialDeploy)" != "" ];then
        echo "sh ${dirName}/${specialDeploy} -g $GAME -m ${Main_server} -s ${mix_server} -d ${game_url}"
        sh ${dirName}/${specialDeploy} -g "$GAME" -m "${Main_server}" -s "${mix_server}" -d "${game_url}" 2>&1
        if [ $? -ne 0 ];then
            echo "error:special change failed!${mix_server}"
        fi
    fi
	#修改攻城掠地后端配置文件并重启gameserver
	sudo -u agent sed -i "/\[${mix_server_yx}_S${mix_server_quhao}\]/d" /app/${GAME}_backstage/socket_gameserver.ini
	sudo -u agent sed -i "\$aTOMCAT_PATH[${mix_server_yx}_S${mix_server_quhao}]=/app/${Main_server}/backend/" /app/${GAME}_backstage/socket_gameserver.ini
    if [ $? -ne 0 ];then
        echo "${mix_server}backstage添加失败"
    fi
	echo "$mix_server deploy succ"
done

cd /app/${Main_server}
rm -rf ${Main_server}_properties ${Main_server}_properties.zip
sudo -u agent sh /app/${GAME}_backstage/start.sh restart
ps x -A -o stime,cmd |grep socket_gameserver|grep -v grep
if [ "$Restart" == "yes" ];then
	#启动游戏
	 > /app/$Main_server/backend/logs/start.out
	sh /app/$Main_server/backend/bin/startup.sh restart
fi
