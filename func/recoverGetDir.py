#!/usr/bin/env python

import os

f = file('/app/remote_file.txt')
file_list = []
for line in f.readlines():
    if 'log' in line:
        file_list.append(line)
f.close()

file_list = ''.join(file_list).split('\n')

new_file = file('/app/log_dir_path.txt','w')

for i in range(len(file_list)):
    for root,dirs,filenames in os.walk(file_list[i]):
        for filename in filenames:
            file_name = os.path.join(root,filename)
            new_file.write(file_name)
            new_file.write('\n')
new_file.close()
