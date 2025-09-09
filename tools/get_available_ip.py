# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 10:50:48 2024

@author: admin
"""

import os
from bs4 import BeautifulSoup
from datetime import datetime
from time import sleep
import requests
import ssl
from tcping import Ping
import json

import webbrowser

ssl._create_default_https_context = ssl._create_unverified_context

site = 'github.com'

cur_url = 'https://site.ip138.com/domain/read.do?domain=' + site
pre_url = 'https://site.ip138.com/' +site

def get_ip(pre_url): #获取历史解析记录
    url = pre_url
    headers =  {
        "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
    }
    
    res = requests.get(url=url, headers=headers)
    sleep(3)
    soup = BeautifulSoup(res.content, 'html.parser')
    
    cont = soup.find('div',attrs={'id':'J_ip_history'}).find_all('a')
    ips = []
    for li in cont:
        
        ips.append(li.get_text())
    return ips


def get_curip(cur_url): #获取当前解析记录
    url = cur_url
    headers =  {
        "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
    }
    
    res = requests.get(url=url, headers=headers)    
    json_ip = res.json()
    
    ips = json_ip['data']
    iplist = []
    for ip in ips :
        iplist.append(ip['ip'])
        
    return iplist

def pingip(ipAddress):
    ping = Ping(ipAddress, 80,3) # 地址、端口、超时时间
    ping.ping(2) # ping命令执行次数

    res = ping.result.table # 以表格形式展现（ping.result.raw  # 原始形态，ping.result.rows  # 行显示）
    ret = ping.result.raw
    retlist = list(ret.split('\n'))
    loss = retlist[2].split(',')[3].split(' ')[1]  # 获取丢包率
    ip = retlist[1].split(' ')[1].split('[')[0]
    return ip, loss
    

def main():
    webbrowser.open((pre_url)) # 获取访问时间戳
    sleep(2)                
    ips_his = get_ip(pre_url)
    ips = get_curip(cur_url)
    iplist = {}
    
    for ip in ips:
        try:
            ip, loss = pingip(ip)
            iplist[ip]=loss
            if float(loss.strip('%')) >= 70:
                print(f"\n{'='*30}> {ip}\n")
        except:
            pass
    
    print(iplist)
    for key, value in iplist.items():
        if float(value.strip('%')) >= 70: 
            print(key)

    print("*"*30)
    for ip in ips_his:
        try:
            ip, loss = pingip(ip)
            iplist[ip]=loss
            if float(loss.strip('%')) >= 70:
                print(f"\n{'='*30}> {ip}\n")            
        except:
            pass
    
    print(iplist)
    for key, value in iplist.items():
        if float(value.strip('%')) >= 70: 
            print(key)
        
    

if __name__ == '__main__':
    # print(datetime.now().strftime('%m-%d'))
    main()
