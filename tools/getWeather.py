# -*- coding: utf-8 -*-
"""
Created on Mon Mar 24 14:56:46 2025

@author: admin
"""

import requests

from bs4 import BeautifulSoup

from win10toast import  ToastNotifier

import time



def get_weather():

    url = "https://www.weather.com.cn/weather/101260101.shtml"
    
    response = requests.get(url)
    
    soup = BeautifulSoup(response.content, 'html.parser')

    weather = soup.find('p', class_='wea').text
    
    temp = soup.find('p', class_='tem').text.strip()
    wind = soup.find('p', class_='win').text.strip()

    
    return f"{weather}, 温度: {temp}, 风力: {wind}"



def send_notification(message):

    toaster = ToastNotifier()
    
    toaster.show_toast("今日天气", message, duration=10)



if __name__ == "__main__":

    while True:
    
        weather_info = get_weather()
        
        send_notification(weather_info)
        
        time.sleep(60) # 每天执行一次