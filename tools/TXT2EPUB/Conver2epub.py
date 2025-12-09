# -*- coding: utf-8 -*-
"""
模块说明：提供TXT与EPUB格式互转、EPUB转MOBI格式的功能
创建时间：2023年8月1日 09:04:38
作者：etony.an@gmail.com
"""
import ebooklib
from ebooklib import epub
#from pymobi import  mobi
from bs4 import BeautifulSoup
import re
import os
import datetime
from opencc import OpenCC  # 用于简繁体转换（需安装opencc-python-reimplemented）
# from kindlestrip import KindleStrip
from pymobi import BookMobi
######

"""
纯 Python 把 .mobi 转 .txt，不依赖 Calibre
"""
import shutil
from pathlib import Path
import  mobi
# https://github.com/iscc/mobi
######


class Conver2epub():
    """
    TXT文件转换为EPUB格式的处理类
    """
    def __init__(self, txtfile, epubfile):
        """
        初始化转换类
        
        参数:
            txtfile (str): 输入的TXT文件路径
            epubfile (str): 输出的EPUB文件路径
        """
        self.txtfile = txtfile # 输入TXT文件路径
        self.epubfile = epubfile # 输出EPUB文件路径
        self.id_epub = 'id_etony.an@gmail.com'  # EPUB唯一标识
        self.title = 'epub'  # 书籍标题
        self.language = 'cn'  # 语言类型（中文）
        self.author = 'etony.an@gmail.com'  # 作者信息
        self.cover = 'cover.jpeg'  # 封面图片路径
        self.encode = 'utf-8'  # 文件编码
        # 章节匹配正则表达式（匹配以第/卷开头，包含数字/汉字的章节标题）
        self.reg = r'^\s*([第卷][0123456789一二三四五六七八九十零〇百千两]*[章回部节集卷].*)\s*'

    def set_reg(self, reg):
        """设置章节匹配的正则表达式"""
        self.reg = reg

    def set_cover(self, cover):
        """设置封面图片路径"""
        self.cover = cover

    def set_author(self, author):
        """设置作者信息"""
        self.author = author

    def set_title(self, title):
        """设置书籍标题"""
        self.title = title

    def set_identifier(self, id_epub):
        """设置EPUB的唯一标识"""
        self.id_epub = id_epub

    def set_encode(self, encode):
        """设置文件编码格式"""
        self.encode = encode

    def get_dir(self):
        """
        解析TXT文件内容，按章节分割
        
        返回:
            list: 章节标题列表（仅标题部分）
        """
        text_file_path = self.txtfile

        with open(text_file_path, 'r', encoding=self.encode, errors='replace') as f:
            content = f.read().strip()  # 去除首尾空白
            # 英文章节
            # regex = "^\s*Chapter\s*[0123456789IVX]*"
            # 中文章节
            regex = self.reg # 使用预设的章节匹配正则
            # 按正则分割内容，结果格式：['', '章节1标题', '章节1内容', '章节2标题', '章节2内容', ...]
            splits = re.split(regex, content, flags=re.M)

            # 按章节分组[(章节1标题,章节1内容）,(章节2标题,章节2内容),...]
            # 提取章节标题（从分割结果中每隔一个元素取标题）
            items = [splits[i]
                     for i in range(1, len(splits) - 1, 2)]

        return items

    def conver(self):
        """执行TXT到EPUB的转换主流程"""
        # 创建EPUB书籍对象        
        book = epub.EpubBook()

        # 设置EPUB元数据
        book.set_identifier(self.id_epub)  # 唯一标识
        book.set_title(self.title)  # 标题
        book.set_language(self.language)# 语言
        # 添加创建时间元数据
        book.add_metadata('DC', 'date', str(datetime.datetime.now()))
        book.add_metadata('DC', 'contributor', 'etony.an@gmail.com')# 贡献者
        # 描述信息
        book.add_metadata('DC', 'description',
                          '请注意，该EPUB文档由TXT文本文件转换生成，原始内容源于互联网。')

        book.add_author(self.author)# 添加作者

        # 如果封面文件存在，设置封面
        # book.add_author('作者2', file_as='作者2', role='ill', uid='coauthor')

        if os.path.exists(self.cover):
            book.set_cover("cover.jpeg", open(self.cover, 'rb').read())

        # 添加默认的NCX（导航目录）和Nav（导航文件）
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # define CSS style
        # style = 'pre{white-space:pre-wrap;background:#f7f9fa;padding:10px 15px;color:#263238;line-height:1.6;font-size:13px;border-radius:3px margin-top: 0;margin-bottom:1em;overflow:auto}b,strong{font-weight:bolder}#title{font-size:16px;color:#212121;font-weight:600;margin-bottom:10px}hr{height:10px;border:0;box-shadow:0 10px 10px -10px #8c8b8b inset}'
        
        # 定义EPUB的CSS样式（控制书籍显示格式）
        style = '''
        @namespace epub "http://www.idpf.org/2007/ops";

        body {
            font-family: Cambria, Liberation Serif, Bitstream Vera Serif, Georgia, Times, Times New Roman, serif;
        }
        
        h1 {
              text-align: left;
              text-transform: uppercase;
              text-indent: 2em;
              font-family: 微软雅黑;
              font-weight: bold; 
              color:#D2691E;
              line-height: 300%; 
              margin: 30px 0 0 0;

        }
        
        h2 {
              text-align: left;
              text-transform: uppercase;
              text-indent: 2em;
              font-family: 微软雅黑;
              font-weight: bold; 
              color:#D2691E;
              line-height: 240%; 
              margin: 20px 0 0 0;

        }
        
        p {
              text-indent: 1.25em;
              margin: 0;
              widows: 2;
              orphans: 2; 

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
        # 创建CSS样式项并添加到书籍
        nav_css = epub.EpubItem(
            uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
        # add CSS file
        book.add_item(nav_css)

        # 初始化书籍装订顺序（先放封面）
        book.spine = ['cover']

        text_file_path = self.txtfile

        with open(text_file_path, 'r', encoding=self.encode) as f:
            content = f.read()  # 章节匹配正则
            # 分割内容为标题和内容交替的列表
            
            # 英文章节
            # regex = "^\s*Chapter\s*[0123456789IVX]*"
            # 中文章节
            regex = self.reg
            # 分割成［'','章节1标题','章节1内容','章节2标题','章节2内容',......］
            splits = re.split(regex, content, flags=re.M)

            # 按章节分组[(章节1标题,章节1内容）,(章节2标题,章节2内容),...]
            # 组合成(标题, 内容)的元组列表
            items = [(splits[i], splits[i + 1])
                     for i in range(1, len(splits) - 1, 2)]

            # 按step章节分组，组成　[[(章节标题,章节内容）,(章节标题,章节内容)],.....]
            # 后续写入压缩文件时，按分组作为一个xhtml文件
            # print(items[0][1].replace(chr(10), '<br>').replace(chr(160), ''))
            # create chapter
            # 遍历章节列表，创建EPUB章节
            for item in items:
                str_title = item[0]  # 章节标题
                # 处理章节内容：换行符转<br>，去除不间断空格
                str_content = item[1].replace(
                    chr(10), '<br>').replace(chr(160), '')
                # 创建XHTML格式的章节对象
                chapter = epub.EpubHtml(
                    title=str_title, file_name=str_title + '.xhtml', lang='hr')
                # 设置章节内容（标题用h2标签，内容用p标签）
                chapter.content = u'<h2>' + str_title + '</h2><p>' + str_content + '</p>'
                # 应用CSS样式
                chapter.add_item(nav_css)

                # 将章节添加到书籍
                book.add_item(chapter)
                
                # 添加到目录（TOC）
                book.toc.append(
                    epub.Link(str_title + '.xhtml', str_title, 'intro'))
                # 添加到装订顺序
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

        # 写入EPUB文件
        epub.write_epub(self.epubfile, book, {})


class Conver2txt():
    """EPUB文件转换为TXT格式的处理类"""
    def __init__(self, epubfile, txtfile, code='utf-8'):
        """
        初始化转换类
        
        参数:
            epubfile (str): 输入的EPUB文件路径
            txtfile (str): 输出的TXT文件路径
            code (str): 输出文件编码，默认utf-8
        """
        self.txtfile = txtfile  # 输出TXT文件路径
        self.epubfile = epubfile # 输入EPUB文件路径
        self.code = code # 编码格式
        self.dirname, filename = os.path.split(txtfile)  # 解析输出目录

        # 读取EPUB书籍对象
        self.book = epub.read_epub(self.epubfile)

    def set_code(self, code='utf-8'):
        """设置输出文件的编码格式"""
        self.code = code

    def modi(self, bookinfo):
        """
        修改EPUB元数据并重新保存
        
        参数:
            bookinfo (dict): 包含书籍元数据的字典，需包含title、date、creator、contrib、filename键
        """
        # 设置元数据（标题、日期、作者、贡献者、描述

        self.book.set_unique_metadata('DC', 'title', bookinfo['title'])
        # self.book.set_language(self.language)
        self.book.set_unique_metadata('DC', 'date', bookinfo['date'])
        self.book.set_unique_metadata('DC', 'creator', bookinfo['creator'])
        self.book.set_unique_metadata('DC', 'contributor', bookinfo['contrib'])
        self.book.set_unique_metadata('DC', 'description',
                                      '请注意，该EPUB文档由TXT文本文件转换生成，原始内容源于互联网。')
        # 重建书签
        # toc = []

        # for item in self.book.get_items():
        #     if item.get_type()== ebooklib.ITEM_DOCUMENT:

        #         toc.append(epub.Link(item.get_name(), item.get_id(), 'intro'))

        # self.book.toc = tuple(toc)
        # 重新写入EPUB文件
        epub.write_epub(bookinfo['filename'], self.book, {})

    def conver(self, fanjian=False):
        """
        将EPUB转换为单TXT文件
        
        参数:
            fanjian (bool): 是否进行繁简转换（True为繁体转简体）
        """
        # 以追加模式打开TXT文件
        with open(self.txtfile, 'a', encoding='utf-8') as f:
            # 遍历EPUB中的所有项目
            for item in self.book.get_items():
                # print(
                #     f'item类型:  {item.get_type()} name: {item.get_name()} id: {item.get_id()}')
                # 处理封面图片
                if ((item.get_type() == ebooklib.ITEM_IMAGE)
                    or (item.get_type() == ebooklib.ITEM_COVER)
                    ) and ((item.get_name().find('cover') >= 0)
                           or (item.id.find('cover') >= 0)):
                    # 解析封面文件扩展名       
                    file_name, file_extension = os.path.splitext(
                        item.get_name())
                    # 封面保存路径（输出目录下的cover+扩展名）
                    coverpath = os.path.join(
                        self.dirname, 'cover'+file_extension)
                    # if  not os.path.exists(coverpath): os.mkdir(coverpath)
                    # 写入封面图片
                    with open(coverpath, 'wb') as ff:
                        ff.write(item.get_content())
                        # print('cover 已提取')
                # 处理文档内容（章节文本）        
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    # 解析HTML内容
                    soup = BeautifulSoup(
                        item.get_content().decode('utf-8'), 'xml')
                    # 繁简转换（如果需要）
                    if fanjian:
                        cc = OpenCC('t2s')  # 繁体转简体
                        f.write(cc.convert(soup.text))

                    else:
                        f.write(soup.text)
                    # 写入章节结束标记
                    f.write('(-本章结束-)')

                    '''
                    ITEM_UNKNOWN = 0
                    ITEM_IMAGE = 1
                    ITEM_STYLE = 2
                    ITEM_SCRIPT = 3
                    ITEM_NAVIGATION = 4
                    ITEM_VECTOR = 5
                    ITEM_FONT = 6
                    ITEM_VIDEO = 7
                    ITEM_AUDIO = 8
                    ITEM_DOCUMENT = 9
                    ITEM_COVER = 10
                    '''

    def conver_chapter(self, fanjian=False):
        """
        将EPUB按章节转换为多个TXT文件
        
        参数:
            fanjian (bool): 是否进行繁简转换（True为繁体转简体）
        """
        cur_dir = os.path.dirname(self.txtfile) # 输出目录
        # 解析文件名（不含扩展名）和扩展名
        filename = os.path.splitext(os.path.basename(self.txtfile))[0]
        ext = os.path.splitext(self.txtfile)[1]
        charpter_numb = 0 # 章节计数器
        print(f'{cur_dir}  {filename}  {ext} ')
        print(self.txtfile)
        
        # 遍历EPUB中的所有项目
        for item in self.book.get_items():
            # print(
            #     f'item类型:  {item.get_type()} name: {item.get_name()} id: {item.get_id()}')
            # 处理封面图片（同conver方法）
            if ((item.get_type() == ebooklib.ITEM_IMAGE)
                or (item.get_type() == ebooklib.ITEM_COVER)
                ) and ((item.get_name().find('cover') >= 0)
                       or (item.id.find('cover') >= 0)):
                file_name, file_extension = os.path.splitext(
                    item.get_name())
                coverpath = os.path.join(
                    self.dirname, 'cover'+file_extension)
                # if  not os.path.exists(coverpath): os.mkdir(coverpath)

                with open(coverpath, 'wb') as ff:
                    ff.write(item.get_content())
                    # print('cover 已提取')
                    
            # 处理文档内容（按章节生成文件）        
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                # 解析HTML内容
                soup = BeautifulSoup(
                    item.get_content().decode('utf-8'), 'xml')
                charpter_numb = charpter_numb + 1  # 章节计数+1
                # 章节文件路径（目录+原文件名+章节号+扩展名）
                file_charpter = os.path.join(
                    cur_dir, f'{filename}{charpter_numb}{ext}')
                # 写入章节内容
                with open(file_charpter, 'a', encoding='utf-8') as f:
                    if fanjian:
                        cc = OpenCC('t2s')
                        f.write(cc.convert(soup.text))

                    else:
                        f.write(soup.text)

    def get_info(self):
        """
        获取EPUB书籍的元数据
        
        返回:
            dict: 包含标题、作者、贡献者、日期的字典
        """
        # 初始化元数据字典（默认值）
        # book = epub.read_epub(self.epubfile)
        book_info = {'title': '未知', 'creator': 'etony.an@gmail.com',
                     'contrib': 'etony.an@gmail.com', 'date': '1000-10-10 10:10:10', }
        # 从EPUB中提取元数据
        try:
            book_info['title'] = self.book.get_metadata('DC', 'title')[0][0]
            book_info['creator'] = self.book.get_metadata('DC', 'creator')[
                0][0]
            book_info['contrib'] = self.book.get_metadata(
                'DC', 'contributor')[0][0]
            book_info['date'] = self.book.get_metadata('DC', 'date')[0][0]
        except:
            # 提取失败时使用默认值
            pass
        return book_info

    def get_cover(self):
        """
        获取EPUB中的封面图片内容
        
        返回:
            bytes: 封面图片的二进制数据；如果未找到则返回None
        """
        # 尝试通过ID获取封面        
        # book = epub.read_epub(self.epubfile)
        cover = self.book.get_item_with_id('cover')
        if (cover.get_type() == ebooklib.ITEM_IMAGE) or (cover.get_type() == ebooklib.ITEM_COVER):
            return cover.get_content()

        # 尝试通过另一ID获取封面
        cover = self.book.get_item_with_id('cover-img')
        if (cover.get_type() == ebooklib.ITEM_IMAGE) or (cover.get_type() == ebooklib.ITEM_COVER):
            return cover.get_content()

        # 尝试从封面类型项目中获取
        items = self.book.get_items_of_type(ebooklib.ITEM_COVER)
        if len(items):
            return items[1].get_content()

        # 尝试从图片类型项目中查找含"cover"名称的图片
        items = self.book.get_items_of_type(ebooklib.ITEM_IMAGE)
        for item in items:
            if (item.get_name().find('cover') >= 0):
                return item.get_content()


class epub2mobi():
    """EPUB文件转换为MOBI格式的处理类（未完全实现）"""
    def __init__(self, epubfile, mobifile, code='utf-8'):
        """
        初始化转换类
        
        参数:
            epubfile (str): 输入的EPUB文件路径
            mobifile (str): 输出的MOBI文件路径
            code (str): 编码格式，默认utf-8
        """
        self.mobifile = mobifile # 输出MOBI文件路径
        self.epubfile = epubfile # 输入EPUB文件路径
        self.code = code # 编码格式
        self.dirname, self.filename = os.path.split(epubfile)  # 解析输入目录和文件名
        
        # 读取EPUB书籍对象
        self.book = epub.read_epub(self.epubfile)

    def e2mobi(self):
        """EPUB转MOBI的方法（基于pymobi，暂未完善）"""
        # 获取书籍标题和作者        
        title = self.book.get_metadata("DC", "title")[0][0]
        author = self.book.get_metadata("DC", "creator")[0][0]
        
        # 创建MOBI书籍对象（需要pymobi库支持）
        mobi_book = mobi.MobiBook()
        
        # 遍历EPUB中的文档内容，添加到MOBI章节
        for item in self.book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                print('==================================')
                print('NAME : ', item.get_name())
                print('----------------------------------')
                print(item.get_content().decode('utf-8'))
                print('==================================')

                mobi_book.add_chapter(
                    item.get_name(), item.get_content().decode('utf-8'))
                
        # 保存MOBI文件
        mobi_book.save(self.mobifile)

    def convert_epub_to_mobi(self):
        """EPUB转MOBI的备用方法（基于KindleStrip，暂未完善）"""
        # 使用ebooklib读取EPUB文件        
        book = ebooklib.epub.read_epub(self.epubfile)

        # 使用KindleStrip进行转换
        # ks = KindleStrip()
        # ks.input_file = self.epubfile
        # ks.output_file = self.mobifile
        # ks.strip()

        # print(f"转换完成，MOBI文件已保存到：{self.mobifile}")
        #         content += item.get_content().decode('utf-8')
        # # for item_id, href in self.book.spine:
        # #     item = self.book.get_item_with_id(item_id)
        # #     print(item)
        # #     content += item.get_content()

        # # 创建MOBI文件
        # km = kindle_maker.KM(self.mobifile)
        # km.set_title(title)
        # km.set_author(author)
        # km.add_chapter("Chapter 1", content)
        # km.make()
        
    def mobi_to_txt(self, mobi_file_path: str, txt_file_path: str = None) -> bool:
        """
        将MOBI文件转换为TXT文件
        :param mobi_file_path: 输入的MOBI文件路径
        :param txt_file_path: 输出的TXT文件路径，若为None则默认与MOBI同目录、同名
        :return: 转换成功返回True，失败返回False
        """
        # 校验输入文件是否存在
        if not os.path.exists(mobi_file_path):
            print(f"错误：MOBI文件不存在，路径为 {mobi_file_path}")
            return False
    
        # 处理输出路径
        if txt_file_path is None:
            mobi_dir = os.path.dirname(mobi_file_path)
            mobi_name = os.path.splitext(os.path.basename(mobi_file_path))[0]
            txt_file_path = os.path.join(mobi_dir, f"{mobi_name}.txt")
    
        try:
            # 读取MOBI文件
            with open(mobi_file_path, 'rb') as mobi_f:
                mobi_data = mobi_f.read()
                mobi = BookMobi(mobi_data)
    
            # 提取文本内容（部分MOBI可能分章节，需遍历拼接）
            full_text = []
            # 先添加书籍元数据（可选）
            full_text.append(f"书名：{mobi.title if mobi.title else '未知'}")
            full_text.append(f"作者：{mobi.author if mobi.author else '未知'}")
            full_text.append("=" * 50)  # 分隔符
            full_text.append("\n")
    
            # 提取正文内容
            content = mobi.get_text()
            if content:
                full_text.append(content)
            else:
                print("警告：未从MOBI文件中提取到正文内容")
    
            # 写入TXT文件
            with open(txt_file_path, 'w', encoding='utf-8') as txt_f:
                txt_f.write("\n".join(full_text))
    
            print(f"转换成功！TXT文件已保存至：{txt_file_path}")
            return True
    
        except Exception as e:
            print(f"转换失败，错误信息：{str(e)}")
            return False


    def convert_mobi_to_txt(mobi_path: Path, txt_path: Path = None) -> Path:
        # https://github.com/iscc/mobi
        if txt_path is None:
            txt_path = mobi_path.with_suffix('.txt')
    
        # 1. 解压到临时目录
        tmpdir, filepath = mobi.extract(mobi_path)

    
        # 2. 找到 html 主文件（content.opf 所在的目录）
        html_files = sorted(tmpdir.rglob('*.html')) + sorted(tmpdir.rglob('*.htm'))
        if not html_files:
            raise RuntimeError('未能在解压目录里找到 html 文件')
    
        # 3. 合并所有 html 并提取纯文本
        text_parts = []
        for hf in html_files:
            soup = BeautifulSoup(hf.read_bytes(), 'lxml')
            text_parts.append(soup.get_text(separator='\n', strip=True))
    
        # 4. 写出 txt
        txt_path.write_text('\n'.join(text_parts), encoding='utf-8')
    
        # 5. 清理临时文件
        shutil.rmtree(tmpdir, ignore_errors=True)
        return txt_path




# if __name__ == "__main__":

#     cover2 = Conver2epub('从前有座灵剑山.txt', '从前有座灵剑山.epub')
#     cover2.conver()
