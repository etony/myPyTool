# -*- coding: utf-8 -*-
"""
Created on Tue Jul 18 14:25:33 2023

@author: admin
"""

from ebooklib import epub
import os

book = epub.EpubBook()

# set metadata
book.set_identifier('id123456')
book.set_title('epub')
book.set_language('cn')

book.add_author('作者')
# book.add_author('作者2', file_as='作者2', role='ill', uid='coauthor')
book.set_cover("cover.jpeg", open('cover.jpeg', 'rb').read())

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
nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
# add CSS file
book.add_item(nav_css)


book.spine= ['cover']

# create chapter
for ch in range(10):
    c1 = epub.EpubHtml(title='章节' + str(ch), file_name='chap_' + str(ch) +'.xhtml', lang='hr')
    c1.content=u'<h1>第' + str(ch) +'章</h1><p>第' + str(ch) +'章内容.</p>'
    
    # add chapter
    book.add_item(c1)

# define Table Of Contents
    book.toc.append(epub.Link('chap_' + str(ch) +'.xhtml', '第' + str(ch) +'章', 'intro'))
    book.spine.append(c1)



# basic spine


# write to the file
epub.write_epub('测试.epub', book, {})