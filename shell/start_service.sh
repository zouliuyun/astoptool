#!/bin/bash

for dir in $(ls -l /app | grep "gcmob*" | awk '{print $NF}')
do
    if [ -e "/app/${dir}/bin/startup.sh" ] && [ -x "/app/${dir}/bin/startup.sh" ]
    then
        sh /app/${dir}/bin/startup.sh start
    fi
done
