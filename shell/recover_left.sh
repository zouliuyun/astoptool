#!/bin/bash

echo -e "\033[35m远程机器/app目录下有如下目录:\033[0m"
cat /app/remote_file.txt | awk -F '/' '{print $3}' | sort | uniq | while read line;
do
    echo -e "\033[1;33m$line\033[0m"
done
echo -e "\033[31m\t\t\t如还有目录需拷贝，请重新执行该脚本：python copy_file.py -h\033[0m"
