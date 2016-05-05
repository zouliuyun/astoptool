#!/usr/bin/env python
#-*- coding:utf8 -*-

import MySQLdb

class mysql:
    def __init__(self,host,username,password,database,port=3306):
        self.connect = MySQLdb.connect(host=host,user=username,passwd=password,port=port,db=database)
        self.cursor = self.connect.cursor()
    def query(self,queryStr):
        self.cursor.execute(queryStr)
        return self.cursor.fetchall()
