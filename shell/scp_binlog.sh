#!/bin/bash

CUURENT_DATE=$(date +%F)

MYSQL_DIR=$(grep "^innodb_data_home_dir" /etc/my.cnf)
cd $MYSQL_DIR
for line in $(cat  mysql-bin.index)
do
    stat $line | grep -E "^Modify:\s*$CURRENT_DATE" > /dev/null
    if [ $? -eq 0 ];then
        scp $line root@${local_host} $MYSQL_DIR
    fi
done
