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

site = 'zh.zlibrary-asia.se'

cur_url = 'https://site.ip138.com/domain/read.do?domain=' + site
pre_url = 'https://site.ip138.com/' +site

def get_ip(pre_url):
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


def get_curip(cur_url):
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
    ping = Ping(ipAddress, 80,3)
    ping.ping(3)

    res = ping.result.table
    ret = ping.result.raw
    retlist = list(ret.split('\n'))
    loss = retlist[2].split(',')[3].split(' ')[1]  # 获取丢包率
    ip = retlist[1].split(' ')[1].split('[')[0]
    return ip, loss
    

def main():
    webbrowser.open((pre_url))
    sleep(2)                
    ips = get_ip(pre_url)
    ips = get_curip(cur_url)
    iplist = {}
    
    for ip in ips:
        try:
            ip, loss = pingip(ip)
            iplist[ip]=loss
        except:
            pass
    
    for key, value in iplist.items():
        if float(value.strip('%')) >= 70: 
            print(key)
        
    

if __name__ == '__main__':
    # print(datetime.now().strftime('%m-%d'))
    main()
