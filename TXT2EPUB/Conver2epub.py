# -*- coding: utf-8 -*-
"""
Created on Tue Aug  1 09:04:38 2023

@author: admin
"""
from ebooklib import epub
# import os
import re


class Conver2epub():
    def __init__(self, txtfile, epubfile):
        self.txtfile = txtfile
        self.epubfile = epubfile
        self.id_epub = 'id_etony.an@gmail.com'
        self.title = 'epub'
        self.language = 'cn'
        self.author = 'etony.an@gmail.com'
        self.cover = 'cover.jpeg'
        self.encode = 'utf-8'
        self.reg = r'^\s*([第卷][0123456789一二三四五六七八九十零〇百千两]*[章回部节集卷].*)\s*'

    def set_reg(self, reg):
        self.reg = reg

    def set_cover(self, cover):
        self.cover = cover

    def set_author(self, author):
        self.author = author

    def set_title(self, title):
        self.title = title

    def set_identifier(self, id_epub):
        self.id_epub = id_epub
        
    def set_encode(self,encode):
        self.encode=encode
    def get_dir(self):
        text_file_path = self.txtfile

        with open(text_file_path, 'r', encoding=self.encode) as f:
            content = f.read()
            # 英文章节
            # regex = "^\s*Chapter\s*[0123456789IVX]*"
            # 中文章节
            regex = self.reg
            # 分割成［'','章节1标题','章节1内容','章节2标题','章节2内容',......］
            splits = re.split(regex, content, flags=re.M)

            # 按章节分组[(章节1标题,章节1内容）,(章节2标题,章节2内容),...]
            items = [splits[i]
                     for i in range(1, len(splits) - 1, 2)]
        
        return items

    def conver(self):
        book = epub.EpubBook()

        # set metadata
        book.set_identifier(self.id_epub)
        book.set_title(self.title)
        book.set_language(self.language)
        book.add_author(self.author)
        # book.add_author('作者2', file_as='作者2', role='ill', uid='coauthor')
        book.set_cover("cover.jpeg", open(self.cover, 'rb').read())

        # add default NCX and Nav file
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # define CSS style
        # style = 'pre{white-space:pre-wrap;background:#f7f9fa;padding:10px 15px;color:#263238;line-height:1.6;font-size:13px;border-radius:3px margin-top: 0;margin-bottom:1em;overflow:auto}b,strong{font-weight:bolder}#title{font-size:16px;color:#212121;font-weight:600;margin-bottom:10px}hr{height:10px;border:0;box-shadow:0 10px 10px -10px #8c8b8b inset}'

        style = '''
        @namespace epub "http://www.idpf.org/2007/ops";

        body {
            font-family: Cambria, Liberation Serif, Bitstream Vera Serif, Georgia, Times, Times New Roman, serif;
        }

        h2 {
              text-align: left;
              text-transform: uppercase;
              font-weight: 200;     
        }

        ol {
                list-style-type: none;
        }

        ol > li:first-child {
                margin-top: 0.3em;
        }


        nav[epub|type~='toc'] > ol > li > ol  {
            list-style-type:square;
        }


        nav[epub|type~='toc'] > ol > li > ol > li {
                margin-top: 0.3em;
        }

        '''

        # nav_css = epub.EpubItem(
        #     uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
        nav_css = epub.EpubItem(
            uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
        # add CSS file
        book.add_item(nav_css)

        book.spine = ['cover']

        text_file_path = self.txtfile

        with open(text_file_path, 'r', encoding="utf-8") as f:
            content = f.read()
            # 英文章节
            # regex = "^\s*Chapter\s*[0123456789IVX]*"
            # 中文章节
            regex = self.reg
            # 分割成［'','章节1标题','章节1内容','章节2标题','章节2内容',......］
            splits = re.split(regex, content, flags=re.M)

            # 按章节分组[(章节1标题,章节1内容）,(章节2标题,章节2内容),...]
            items = [(splits[i], splits[i + 1])
                     for i in range(1, len(splits) - 1, 2)]

            # 按step章节分组，组成　[[(章节标题,章节内容）,(章节标题,章节内容)],.....]
            # 后续写入压缩文件时，按分组作为一个xhtml文件
            # print(items[0][1].replace(chr(10), '<br>').replace(chr(160), ''))
            # create chapter
            for item in items:
                str_title = item[0]
                str_content = item[1].replace(
                    chr(10), '<br>').replace(chr(160), '')
                chapter = epub.EpubHtml(
                    title=str_title, file_name=str_title + '.xhtml', lang='hr')
                chapter.content = u'<h1>' + str_title + '</h1><p>' + str_content + '</p>'

                # add chapter
                book.add_item(chapter)

            # define Table Of Contents
                book.toc.append(
                    epub.Link(str_title + '.xhtml', str_title, 'intro'))
                book.spine.append(chapter)

        # create chapter
        # for ch in range(10):
        #     c1 = epub.EpubHtml(title='章节' + str(ch), file_name='chap_' + str(ch) +'.xhtml', lang='hr')
        #     c1.content=u'<h1>第' + str(ch) +'章</h1><p>第' + str(ch) +'章内容.</p>'
        #     # add chapter
        #     book.add_item(c1)
        # # define Table Of Contents
        #     book.toc.append(epub.Link('chap_' + str(ch) +'.xhtml', '第' + str(ch) +'章', 'intro'))
        #     book.spine.append(c1)

        # basic spine

        # write to the file
        epub.write_epub(self.epubfile, book, {})


if __name__ == "__main__":

    cover2 = Conver2epub('从前有座灵剑山.txt', '从前有座灵剑山2.epub')
    cover2.conver()
