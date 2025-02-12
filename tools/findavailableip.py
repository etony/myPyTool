# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 09:28:20 2025

@author: admin
"""
import re
from bs4 import BeautifulSoup
import requests
import multiping

headers = {
    "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0",
}
step = 5


def is_valid_domain(domain):
    pattern = r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z]{2,})+$"
    return re.match(pattern, domain) is not None


def get_valid_ip(url):
    ips = []

    req = requests.get(url, headers=headers)
    soup = BeautifulSoup(req.text, 'html.parser')
    try:
        content = soup.find('div', attrs={'id': 'J_ip_history'}).find_all('a')
        for cat in content:
            ips.append(cat.get_text())
    except:
        print("\n\033[1;31m无法查询该域名.\033[0m")
    return ips


def get_current_ip(url):
    ips = []
    req = requests.get(url, headers=headers)
    msg = req.json()
    if msg['status']:
        datas = msg['data']
        for data in datas:
            ips.append(data['ip'])

    return ips


def mping(ips, step):
    valid_ip = {}
    length = len(ips)
    for i in range(0, length, step):
        j = i + step
        if j > length:
            j = length
        mp = multiping.MultiPing(ips[i:j])
        try:
            mp.send()
            results, no_results = mp.receive(5)

            for addr, rtt in results.items():
                print(f"{addr} 响应时间为 {rtt} 秒")
                valid_ip[addr]= rtt
            if no_results:
                print(f"\n以下地址没有响应：{', '.join(no_results)}\n")
        except:
            pass
    return valid_ip


def main():
    domain = input('输入查询域名:').strip()
    if is_valid_domain(domain):
        url = ''.join(['https://site.ip138.com/', domain, '/'])
        url_current = ''.join(
            ['https://site.ip138.com/domain/read.do?domain=', domain])

        ips = get_valid_ip(url)
        ips_current = get_current_ip(url_current)
        ip = mping(ips_current+ips, step)
        if len(ip) > 0:
            # 根据响应值排序
            sorted_by_value = dict(sorted(ip.items(), key=lambda item: item[1]))
            print(sorted_by_value)
            print(f"\n该域名的可用ip地址：{', '.join(sorted_by_value)}")
        else:
            print("\n\033[1;31m该域名无可用ip地址.\033[0m")


if __name__ == '__main__':

    main()
