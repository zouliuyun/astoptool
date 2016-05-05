#!/bin/bash
game=$1 
language=$2 
oldyx=$3 
newyx=$4 
official_url=$5 
addiction_url=$6 
bbs_url=$7 
cname=$8 
pay_url=$9 
allow_ip=${10}
#echo $game/$language/$oldyx/$newyx/$official_url/$addiction_url/$bbs_url/$cname/$pay_url/$allow_ip
#exit
moddir=/app/www/$game/newserver/$language
cd $moddir
echo -e 'use template $oldyx!\nstart decompress www properties template...'
special_key_string=(\\\~ \\\! \\\# \\\$ \\\^ \\\*)
key_string=(A B C D E F G H I J K L M N O P Q R S T U V W X Y Z a b c d e f g h i j k l m n o p q r s t u v w x y z 0 1 2 3 4 5 6 7 8 9)
PAY_KEY=""
LOGIN_KEY=""
QUERY_KEY=""
echo "start create keys,please wait:..."
for key in `echo "pay_key login_key query_key"`
    do
        nu0=3
        i=0
        for i in  `seq 0 $nu0`
            do
                s=$((RANDOM%6))
                array0[$i]=${special_key_string[$s]}
                sting0=`echo ${array0[@]}|sed 's/ //g;s/\\\//g'`
            done
        sleep 1
        string_num=({15..18})
        s1=$((RANDOM%4))
        nu1=${string_num[$s1]}
        i=0
        for i in  `seq 0 $nu1`
            do
                s=$((RANDOM%62))
                array1[$i]=${key_string[$s]} #RANDOM是bash shell内置的随机变量，表达式可修改
                #echo ${array1[$i]} #打印验证
            sting1=`echo ${array1[@]}|sed 's/ //g;'`
            done
            if [ "$key" == "pay_key" ];then
                PAY_KEY="$sting0@@($newyx::PAY)@@$sting1"
            elif [ "$key" == "login_key" ];then
                LOGIN_KEY="$sting0@@($newyx::LOGIN)@@$sting1"
            elif [ "$key" == "query_key" ];then
                QUERY_KEY="$sting0@@($newyx::QUERY)@@$sting1"
            fi
done
Unicode_name=`echo "$cname" |/usr/local/jdk/bin/native2ascii`
echo "zzsf2.servername = $cname" |/usr/local/jdk/bin/native2ascii >cname.sed
echo $Unicode_name
echo "zzsf2.pay.key = $PAY_KEY" >pay.sed
echo "zzsf2.login.key = $LOGIN_KEY" >login.sed
echo "zzsf2.query.key = $QUERY_KEY" >query.sed
echo "zzsf2.pay.url = $pay_url" > pay_url.sed
echo "zzsf2.addiction.url = $addiction_url" > addiction_url.sed
echo "create keys&yx to file"
echo "预登录和登录key：$LOGIN_KEY" >${game}_${cname}对接key.txt
echo "充值key：$PAY_KEY" >>${game}_${cname}对接key.txt
echo "查询key：$QUERY_KEY" >>${game}_${cname}对接key.txt
echo "对接的运营商标示为：$newyx" >>${game}_${cname}对接key.txt
mv ${game}_${cname}对接key.txt ./key/
mv pay.sed login.sed query.sed cname.sed pay_url.sed addiction_url.sed ./properties/
echo "properties生成..."
cd $moddir/properties
cp $oldyx.properties $newyx.properties
sed -i "s#zzsf2.redirect.url =.*#zzsf2.redirect.url = $official_url#g" $newyx.properties
sed -i "s#zzsf2.unlogin.redirect.url =.*#zzsf2.unlogin.redirect.url = $official_url#g" $newyx.properties
sed -i "s#zzsf2.servername =.*#zzsf2.servername = $newyx#g" $newyx.properties
sed -i '/zzsf2.pay.url/d' $newyx.properties
sed -i '/支付地址/r pay_url.sed' $newyx.properties
sed -i '/zzsf2.addiction.url/d' $newyx.properties
sed -i '/防沉迷页面/r addiction_url.sed' $newyx.properties
sed -i "s#zzsf2.passed.ip = .*#zzsf2.passed.ip = $allow_ip#g" $newyx.properties
sed -i '/zzsf2.query.key/d' $newyx.properties
sed -i '/查询Key/r query.sed' $newyx.properties
sed -i '/zzsf2.login.key/d' $newyx.properties
sed -i '/登录Key/r login.sed' $newyx.properties
sed -i '/zzsf2.pay.key/d' $newyx.properties
sed -i '/充值Key/r pay.sed' $newyx.properties
sed -i '/zzsf2.servername/d' $newyx.properties
sed -i '/服务器名称/r cname.sed' $newyx.properties
sed -i '/zzsf2.serverflag/d' $newyx.properties
sed -i "/服务器标识/a zzsf2.serverflag = $newyx" $newyx.properties
rm -f pay.sed login.sed query.sed cname.sed pay_url.sed addiction_url.sed
echo "properties生成成功"

echo "template生成..."
cd $moddir/template
if  [ -d backend ];then rm backend -rf ;fi
tar -xzf $oldyx.tgz
if [ $? -eq 0 ];then
    sed -i '/zzsf2.yx =/d' backend/apps/server.properties
    sed -i "/运营商标识/a zzsf2.yx = $newyx" backend/apps/server.properties
    tar -czf $newyx.tgz backend
    if [ $? -ne 0 ];then
        echo "template生成失败"
    else
        echo "template生成成功"
        rm backend -rf
    fi
else
    echo "template生成失败"
fi

echo "www模板生成"
cd $moddir/www
if [ -d www_${newyx} ];then
    cd www_${newyx} && rm * -rf
else
    mkdir www_${newyx}
fi
tar -xzf www_$oldyx.tgz -C www_${newyx}
if [ $? -eq 0 ];then
    cd $moddir/www/www_${newyx}
    sed -i 's#.*您可以尝试.*#\t\t您可以尝试:<a href="'$official_url'" class="index">〈〈返回首页</a>#g' 404.html
    sed -i 's#.*<gameHome.*#\t<gameHome value="'$official_url'" />#g' Config.xml
    sed -i 's#.*<gameBBS.*#\t<gameBBS value="'$bbs_url'" />#g' Config.xml
    tar -zcf www_${newyx}.tgz * && mv www_${newyx}.tgz ../ && cd ../ && rm -rf www_${newyx}
    if [ $? -eq 0 ];then
        echo "www模板生成成功"
    else
        echo "www模板生成失败"
    fi
fi
