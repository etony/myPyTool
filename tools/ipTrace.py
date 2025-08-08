# -*- coding: utf-8 -*-
"""
Created on Fri Aug  8 15:20:17 2025

@author: admin
"""

from scapy.all import *
import requests
import json


ips = []

def traceroute(destination):
    ips = []
    max_hops = 30
    timeout = 2

    for ttl in range(1, max_hops + 1):
        pkt = IP(dst=destination, ttl=ttl) / ICMP()
        reply = sr1(pkt, timeout=timeout, verbose=0)

        if reply is None:
            print(f"{ttl}: 请求超时")
        elif reply.type == 0:
            print(f"{ttl}: 到达目标 {reply.src}")
            break
        else:
            print(f"{ttl}: {reply.src}")
            ips.append(reply.src)

    return ips

def getAddr(ips: list):
    addrs =[]
    url = 'http://whois.pconline.com.cn/ipJson.jsp'
    for ip in ips:
        param = {'ip':ip,
                 'json':'true'
                } 
        ree = requests.get(url, params = param)
        if ree.status_code == 200 :  
            re = json.loads(ree.text.replace("\\"," "))
            #print(re)
            addrs.append(re)
    return addrs

if __name__ == '__main__':
    
    print('请输入目标地址:')
    dest = input()
    
    myips = traceroute(dest)
    
    myaddrs = getAddr(myips)
    
    for ad in myaddrs:
        print(ad['addr'].strip())   


# traceroute('8.8.8.8')
# addr =[]

# url = 'http://whois.pconline.com.cn/ipJson.jsp'
# for ip in ips:    
#     param = {'ip':ip,
#              'json':'true'
#             } 
#     ree = requests.get(url, params = param)
#     if ree.status_code == 200 :  
#         re = json.loads(ree.text.replace("\\"," "))
#         #print(re)
#         addr.append(re)



# print(addr)    
# for ad in addr:
#     print(ad['addr'].strip())    
    
    
    # https://cloud.tencent.com/developer/article/1856340