#!/usr/bin/env python
#~*~coding:utf8~*~
import re,os

def nullCheck(arg):
    if arg == None or str(arg).lower() == "none" or str(arg).lower() == "null" or arg.strip() == "":
        return True
    else:
        return False
def checkNumber(str):
    try:
        int(str)
        return True
    except:
        return False
def checkServer(str):
    if re.match(r'^[0-9a-zA-Z]+_[0-9]+$',str):
        return True
    else:
        return False
def checkIp(str):
    if re.match(r'^(1[0-9]{2}|2[0-4][0-9]|25[0-5]|[0-9]{2}|[0-9])(\.(1[0-9]{2}|2[0-4][0-9]|25[0-5]|[0-9]{2}|[0-9])){3}$',str):
        return True
    else:
        return False
def checkIpList(str):
    if re.match(r'^(1[0-9]{2}|2[0-4][0-9]|25[0-5]|[0-9]{2}|[0-9])(\.(1[0-9]{2}|2[0-4][0-9]|25[0-5]|[0-9]{2}|[0-9])){3}(,(1[0-9]{2}|2[0-4][0-9]|25[0-5]|[0-9]{2}|[0-9])(\.(1[0-9]{2}|2[0-4][0-9]|25[0-5]|[0-9]{2}|[0-9])){3})*$',str):
        return True
    else:
        return False
def checkDatetime(str):
    try:
        import datetime
        datetime.datetime.strptime(str,"%Y-%m-%d %H:%M:%S")
        return True
    except:
        return False
def checkDate(str):
    try:
        import datetime
        datetime.datetime.strptime(str,"%Y-%m-%d")
        return True
    except:
        return False
def checkTime(str):
    try:
        import datetime
        datetime.datetime.strptime(str,"%H:%M:%S")
        return True
    except:
        return False
def checkGame(str):
    if re.match(r'^[0-9a-z]+$',str):
        return True
    else:
        return False
