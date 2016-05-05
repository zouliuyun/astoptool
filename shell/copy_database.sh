#!/bin/bash

SERVERLIST=$1
GAME=$2
BACKUP_DATE=$3
MysqlDBDir=$4

CUURENT_DATE=$(/bin/date +%F)
MYSQL_DIR=$(/bin/grep "^innodb_data_home_dir" /etc/my.cnf|/bin/cut -d'=' -f2|xargs echo)

PATH="/app/dbbk"
TEMP_DIR="${MysqlDBDir}/${BACKUP_DATE}"

DB_DATE=$(/bin/date -d $BACKUP_DATE +"%Y%m%d")

/bin/rm -rf $TEMP_DIR
/bin/mkdir -p $TEMP_DIR


/bin/cd "$TEMP_DIR"
for i in $SERVERLIST
do
    (
    DATABASE="${GAME}_${i}"
    DB_FILE=${DATABASE}_${DB_DATE}.sql.bz2
    /bin/cp ${PATH}/${DATABASE}/${DB_FILE} $TEMP_DIR/
    /usr/bin/bzip2 -k -d $TEMP_DIR/$DB_FILE
    START_TIME=$(/usr/bin/tail -1 $TEMP_DIR/${DATABASE}_${DB_DATE}.sql|/bin/awk -F 'on ' '{print $2}')
    /bin/rm $TEMP_DIR/${DATABASE}_${DB_DATE}.sql
    for line in $(/bin/cat ${MYSQL_DIR}/mysql-bin.index)
    do
        FILE_DATE=$(/usr/bin/stat ${MYSQL_DIR}/$line | /bin/grep "Modify" | /bin/awk '{print $2}')
        if [[ ${BACKUP_DATE} < ${FILE_DATE} ]] || [[ ${BACKUP_DATE} = ${FILE_DATE} ]]
        then
            /usr/local/mysql/bin/mysqlbinlog --start-datetime "$START_TIME" -d ${DATABASE} ${MYSQL_DIR}/$line >> $TEMP_DIR/${DATABASE}.binlog
        fi
    done
    )&
done
wait
