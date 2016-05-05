#!/bin/bash
recoverIp=$1

CURRENT_DATE=$(date +%F)

cat /app/log_dir_path.txt | grep "$CURRENT_DATE" | sort | uniq | while read line;
do
    DIR=`echo $line | awk -F '/[^/]*$' '{print $1}'`
    ssh $recoverIp "mkdir -p $DIR && chown astd.astd $DIR"
    rsync -av $line ${recoverIp}:$DIR
done

