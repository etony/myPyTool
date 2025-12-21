# -*- coding: utf-8 -*-

"""
Module implementing ObtainAvailableIp.
"""

import sys
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QDialog, QApplication
from Ui_obavip import Ui_Dialog

from bs4 import BeautifulSoup
from time import sleep
import requests
import ssl
from tcping import Ping
import webbrowser
import qdarkstyle

ssl._create_default_https_context = ssl._create_unverified_context



class ObtainAvailableIp(QDialog, Ui_Dialog):
    """
    Class documentation goes here.
    """

    def __init__(self, parent=None):
        """
        Constructor

        @param parent reference to the parent widget (defaults to None)
        @type QWidget (optional)
        """
        super().__init__(parent)
        self.setupUi(self)
        self.setFixedSize(self.width(), self.height())  # 固定窗口大小，避免布局错乱
        self.cur_url = 'https://site.ip138.com/domain/read.do?domain=' 
        self.pre_url = 'https://site.ip138.com/'

        
        
    @pyqtSlot()
    def on_pb_getit_clicked(self):
        domain = self.le_domain.text().strip()
        self.cur_url += domain
        self.pre_url += domain
        self.main()
        

    def get_ip(self,pre_url):  # 获取历史解析记录
        url = pre_url
        headers = {
            "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
        }
    
        res = requests.get(url=url, headers=headers)
        sleep(3)
        soup = BeautifulSoup(res.content, 'html.parser')
    
        cont = soup.find('div', attrs={'id': 'J_ip_history'}).find_all('a')
        ips = []
        for li in cont:
    
            ips.append(li.get_text())
        return ips
    
    
    def get_curip(self,cur_url):  # 获取当前解析记录
        url = cur_url
        headers = {
            "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
        }
    
        res = requests.get(url=url, headers=headers)
        json_ip = res.json()
    
        ips = json_ip['data']
        iplist = []
        for ip in ips:
            iplist.append(ip['ip'])
    
        return iplist
    
    
    def pingip(self,ipAddress):
        ping = Ping(ipAddress, 80, 3)  # 地址、端口、超时时间
        ping.ping(2)  # ping命令执行次数
    
        res = ping.result.table  # 以表格形式展现（ping.result.raw  # 原始形态，ping.result.rows  # 行显示）
        print(res)
        ret = ping.result.raw
        retlist = list(ret.split('\n'))
        loss = retlist[2].split(',')[3].split(' ')[1]  # 获取丢包率
        ip = retlist[1].split(' ')[1].split('[')[0]
        return ip, loss
    
    def main(self):
        webbrowser.open((self.pre_url))  # 获取访问时间戳
        sleep(2)
        ips_his = self.get_ip(self.pre_url)
        ips = self.get_curip(self.cur_url)
        self.pt_ip
        iplist = {}
    
        for ip in ips:
            try:
                ip, loss = self.pingip(ip)
                if float(loss.strip('%')) >= 70:
                    iplist[ip] = loss
                    print(f"\n{'='*50}> {ip}\n")
    
            except:
                pass
    
        if len(iplist) >= 1:
            print(f"\n\033[32m{'='*20} 可用IP {'='*20}\033[0m\n")
            for key, value in iplist.items():
                if float(value.strip('%')) >= 70:
                    print(key)
            return
    
        print(f'\n{"*"*50}')
        for ip in ips_his:
            try:
                ip, loss = self.pingip(ip)
                if float(loss.strip('%')) >= 70:
                    iplist[ip] = loss
                    print(f"\n{'='*50}> {ip}\n")
            except:
                pass
        if len(iplist) >= 1:
            print(f"\n\033[32m{'='*20} 可用IP {'='*20}\033[0m\n")
            for key, value in iplist.items():
                if float(value.strip('%')) >= 70:
                    print(key)
            return


if __name__ == "__main__":
    """
    程序入口：初始化PyQt应用，创建主窗口，启动事件循环。
    """
    app = QApplication(sys.argv)  # 初始化PyQt应用
    app.setStyleSheet(qdarkstyle.load_stylesheet()) 
    obavip = ObtainAvailableIp()         # 创建主窗口实例
    obavip.show()               # 显示主窗口
    sys.exit(app.exec())          # 启动事件循环，退出时返回状态码