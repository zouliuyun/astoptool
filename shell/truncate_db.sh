#!/bin/bash
server=$1
yx=$(echo $server|cut -d'_' -f2)
sqlfile=truncate_db.sql
[ -f tables.txt ] && rm -f tables.txt
[ -f  ${sqlfile} ] && rm -f  ${sqlfile}
pandora $server -e  "show  tables"  > tables.txt
if [ $? -ne 0 ];then
    echo "show tables失败！"
    exit 1
fi
cat  tables.txt  | tr -d ' ' |xargs -i  echo truncate table {}";"  >  ${sqlfile}
sed  -i "/truncate table Tables_in_${server};/d"  ${sqlfile}
sed  -i '/truncate table db_version;/d' ${sqlfile}
sed  -i '/truncate table system_notice;/d' ${sqlfile}
sed  -i '/truncate table activity;/d'   ${sqlfile}
echo "update  db_version set  server_time = now();" >> ${sqlfile}
echo "update  db_version set diff_day=0;" >> ${sqlfile}


rm -f tables.txt
