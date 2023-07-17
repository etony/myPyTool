# -*- coding: utf-8 -*-
"""
Created on Mon Jul 17 22:57:53 2023

@author: tony
"""


import os
import re
import zipfile
 
from jinja2 import Environment, FileSystemLoader
 
 
def txt2epub(save_as_path, text_file_path, cover_image_path, bookname, author):
    """
    将文本文件转为epub格式
    :param save_as_path: 保存epub的文件路径
    :param text_file_path: 文本文件路径
    :param cover_image_path: 封面图片路径
    :param bookname: 书名
    :param author：作者
    :return:
    """
    if os.path.exists(text_file_path):
        print("开始转换文件")
        with open(text_file_path, 'r') as f:
            content = f.read()
            # 英文章节
            # regex = "^\s*Chapter\s*[0123456789IVX]*"
            # 中文章节
            regex = r"^\s*([第卷][0123456789一二三四五六七八九十零〇百千两]*[章回部节集卷].*)\s*"
            splits = re.split(regex, content, flags=re.M)
            items = [(splits[i], splits[i + 1]) for i in range(1, len(splits) - 1, 2)]
            if len(items) > 0:
                print("ok")
                tmploader = FileSystemLoader(os.path.abspath('./template/'))
                tmpenv = Environment(loader=tmploader)
 
                book = zipfile.ZipFile(save_as_path, 'w')
                # images
 
                # container.xml
                book.write('./template/META-INF/container.xml', 'META-INF/container.xml')
 
                # text
                nav = tmpenv.get_template("text/nav.html")
                nav_html = nav.render(items=items, bookname=bookname)
                book.writestr('text/nav.html', nav_html)
                print(nav_html)
                part = tmpenv.get_template("text/part.html")
                index = 0
                for item in items:
                    index += 1
                    part_html = part.render(item=item, index=index, bookname=bookname)
                    book.writestr('text/part%s.html' % index, part_html)
 
                # content.opf
                opf = tmpenv.get_template("content.opf")
                content_opf = opf.render(items=items, bookname=bookname, author=author)
                book.writestr('content.opf', content_opf)
 
                # cover.jpeg
                book.write('./template/cover.jpeg', 'cover.jpeg')
                # mimetype
                book.write("./template/mimetype", 'mimetype')
                # page_styles.css
                book.write('./template/page_styles.css', 'page_styles.css')
                # stylesheet.css
                book.write('./template/stylesheet.css', 'stylesheet.css')
                # titlepage.xhtml
                book.write('./template/titlepage.xhtml', 'titlepage.xhtml')
 
                # toc.ncx
                ncx = tmpenv.get_template("toc.ncx")
                toc_ncx = ncx.render(items=items, bookname=bookname)
                book.writestr('toc.ncx', toc_ncx)
                print(toc_ncx)
 
                book.close()
 
                print("ok")
    else:
        print("源文件不存在")
 
    pass


txt2epub('/Users/xulong/Downloads/冰与火之歌.epub', '/Users/xulong/Downloads/冰与火之歌.txt', '', bookname='书名', author='xulong')