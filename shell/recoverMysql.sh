#!/bin/bash

FILENAME=$1
MysqlDBDir=$2
BACKUP_DATE=$3

TEMP_DIR="${MysqlDBDir}/$(date +'%Y%m%d')"

mkdir $TEMP_DIR && cd $TEMP_DIR
cat $FILENAME | while read DATABASE REMOTE_IP
do
    (
    ssh $REMOTE_IP "mkdir -p $TEMP_DIR"
    scp ${DATABASE}_${BACKUP_DATE}.sql ${REMOTE_IP}:${TEMP_DIR}
    scp ${DATABASE}.binlog ${REMOTE_IP}:${TEMP_DIR}

    pandora --update -e 'create database $DATABASE'
    pandora --update -e '$DATABASE' < ${DATABASE}_${BACKUP_DATE}.sql
    if [ "$?" -eq "0" ]
    then
        pandora --update $DATABSE < ${DATABSE}.binlog
    fi
    )&
    ssh $REMOTE_IP "service mysqld start"
done

