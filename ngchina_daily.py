# -*- coding: utf-8 -*-

import requests
import json

ps = 12
timeout = 5

json= {"cmsNews":{"categoryId":18,"isWebsite":"Y"},"pageDomain":{"pageNum":1,"pageSize":ps,"orderByColumn":"publish_time","isAsc":"desc"}}

response = requests.post('http://www.ngchina.com.cn/api/ex/cms/news/list', json=json, timeout=timeout)

if response.status_code == 200:
    res = response.json()
    total = res['total']
    page = round(total/ps)
    print("共 " + str(page) +" 页")
    for pageNum  in range(1, page+1):
        print(pageNum)
        json =  {"cmsNews":{"categoryId":18,"isWebsite":"Y"},"pageDomain":{"pageNum":pageNum,"pageSize":ps,"orderByColumn":"publish_time","isAsc":"desc"}}
        response = requests.post('http://www.ngchina.com.cn/api/ex/cms/news/list', json=json, timeout=timeout)
        if response.status_code == 200:
            res = response.json()
            size = len(res['rows'])
            for i in range(size):
                im = res['rows'][i]
                pichref = im['pic']
                picname = im['title']
                print("{:<20}  {:<}".format(picname, pichref))
                try:
                    pic = requests.get(pichref, timeout=15)
                    if pic.status_code == 200:                    
                        open((picname+'.jpg'),'wb').write(pic.content)
                except:
                    print("图片获取失败。")
                



