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

    wea = soup.findAll('p', class_='wea')
    temp = soup.findAll('p', class_='tem')
    wind = soup.findAll('p', class_='win')
    
    print(f'今天：{wea[0].text}, 温度: {temp[0].text.strip()}, 风力: {wind[0].text.strip()}')
    print(f'明天：{wea[1].text}, 温度: {temp[1].text.strip()}, 风力: {wind[1].text.strip()}')
    print(f'后天：{wea[2].text}, 温度: {temp[2].text.strip()}, 风力: {wind[2].text.strip()}')

    
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