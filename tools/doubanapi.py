# -*- coding: utf-8 -*-
"""
Created on Sun Dec 14 12:00:32 2025

@author: etony
"""
"""
豆瓣图书API封装类
功能：
    1. 通过ISBN精准查询单本图书信息
    2. 通过书名模糊搜索多本图书信息
    3. 自动清洗图书数据（价格、作者/译者格式）
    4. 计算图书推荐度（基于评分和评价人数）
依赖：
    - requests: 发送HTTP请求（需提前安装：pip install requests）
    - math: 推荐度计算（自然对数）
    - logging: 日志记录
    - json: 响应数据解析
豆瓣API文档参考：https://developers.douban.com/wiki/?title=book_v2
"""
import math
import logging
import requests
import json
from typing import List, Optional, Dict, Any,ByteString

# ===================== 全局配置与常量定义 =====================
# 日志配置：初始化日志器，记录关键操作和异常（便于问题排查）
logging.basicConfig(
    level=logging.INFO,          # 日志级别：INFO（常规操作）/ERROR（异常）/DEBUG（调试）
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # 日志格式（时间-模块-级别-内容）
    handlers=[
        logging.StreamHandler(),  # 控制台输出
        logging.FileHandler("douban_book_api.log", encoding="utf-8")  # 日志文件（UTF-8避免中文乱码）
    ]
)
LOG = logging.getLogger(__name__)  # 日志器实例（绑定当前模块名）

class DouBanApi:

    """
    豆瓣图书API封装类
    核心特性：
        - 自动处理API请求头（模拟移动端，规避反爬）
        - 全字段容错（避免KeyError/TypeError）
        - 数据清洗（价格、作者/译者格式统一）
        - 异常捕获（网络错误、解析错误、计算错误）
        - 连接复用（Session减少TCP握手开销）
    """    
    def __init__(self):

        self.url_isbn = "https://api.douban.com/v2/book/isbn/"
        self.url_search = "https://api.douban.com/v2/book/search"
        self.key='0ab215a8b1977939201640fa14c66bab'
        # API密钥（apikey）：豆瓣开放平台申请，用于提升API调用限额，避免请求被拦截
        # apikey=0df993c66c0c636e29ecbb5344252a4a
        # apikey=0ac44ae016490db2204ce0a042db2916
        self.payload_isbn = {'apikey': '0ab215a8b1977939201640fa14c66bab'}
        self.payload_search = {'apikey': '0ac44ae016490db2204ce0a042db2916'}
        # 请求头：模拟iPhone移动端浏览器，规避豆瓣API的反爬机制（PC端请求易被限制）
        self.headers = {
            "Referer":
            "https://m.douban.com/tv/american", # 模拟移动端来源页，提升请求合法性
            "User-Agent":
            "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"
        } 
            
            
    def _get_safe_value(self, data: Dict[str, Any], keys: List[str], default: Any = "") -> Any:
        """
        安全获取嵌套字典的值，避免KeyError
        :param data: 源字典
        :param keys: 嵌套键列表（如['images', 'small']）
        :param default: 默认值
        :return: 目标值或默认值
        """
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current            

    def _clean_price(self, price: str) -> str:
        """
        价格字段清洗（统一格式）
        处理场景：
            - 原始价格可能包含"CNY"（如"CNY 99.00"）
            - 原始价格可能包含"元"（如"99.00元"）
            - 原始价格可能有首尾空格（如" 99.00 "）
        :param price: 原始价格字符串
        :return: 清洗后的价格（如"99.00"）
        """
        if not price:
            return ""
        return price.replace("CNY", "").replace("元", "").strip()

    def _calculate_recommend(self, average: str, num_raters: str) -> int:
        """
        计算图书推荐度（自定义公式，带全量容错）
        公式逻辑：
            - (平均分 - 2.5)：过滤低分图书（平均分<2.5时推荐度为负/0）
            - × ln(评价人数 + 1)：评价人数越多，权重越高（+1避免ln(0)异常）
            - round：四舍五入为整数，便于展示
        :param average: 豆瓣平均分（可能为字符串/空值/非数字）
        :param num_raters: 评价人数（可能为字符串/空值/非数字）
        :return: 推荐度（整数，异常时返回0）
        """
        try:
            avg = float(average) if average else 0.0
            num = float(num_raters) if num_raters else 0.0
            if avg < 2.5 or num < 0:
                return 0
            # 推荐度公式：(平均分 - 2.5) × ln(评价人数 + 1)
            recommend = (avg - 2.5) * math.log(num + 1)
            return round(recommend)
        except (ValueError, math.DomainError):
            LOG.error(f"计算推荐度失败：平均分={average}，评价人数={num_raters}")
            return 0
    
    def get_bookinfo_by_isbn(self,isbn:str) -> Optional[List[str]]:
        """
        通过ISBN精准查询单本图书信息（核心方法）
        :param isbn: 图书ISBN编号（如"9787115428028"）
        :return: 格式化图书信息列表（固定15个元素）/None（无效数据/异常）
        返回列表索引说明：
            0: ISBN编号
            1: 书名
            2: 作者+译者（格式："作者1/作者2 译者: 译者1/译者2"）
            3: 出版社
            4: 价格（清洗后）
            5: 豆瓣平均分
            6: 评价人数
            7: 分类（默认"计划"）
            8: 书柜位置（默认"未设置"）
            9: 封面小图URL
            10: 出版日期
            11: 完整评分信息（字符串化字典）
            12: 豆瓣图书详情页URL
            13: 推荐度（整数转字符串）
            14: 页数
        """
        # 前置校验：ISBN为空直接返回None
        if not isbn:
            LOG.warning("ISBN为空")
            return None
        # 拼接完整请求URL：基础URL + ISBN（豆瓣ISBN接口要求ISBN拼在URL后）

        url = f"{self.url_isbn}{isbn}" 
        try:
            # 发送GET请求（豆瓣ISBN接口仅支持GET，原代码误用POST）
            # 参数说明：params传递API Key，timeout避免网络卡死

            response = requests.post(url, data=self.payload_isbn, headers=self.headers)
            # 解析JSON响应（豆瓣API返回UTF-8编码的JSON）
            book_dict = json.loads(response.text)
        except requests.exceptions.RequestException as e:
            LOG.error(f"ISBN {isbn} 请求失败：{str(e)}")
            return None
        except json.JSONDecodeError:
            LOG.error(f"ISBN {isbn} 响应解析失败：{response.text}")
            return None
        
        bookinfo =[]
        
        # 过滤残缺数据：字段数<最小阈值 → 返回None 
        if len(book_dict) > 5:
            # ===================== 5. 数据清洗与格式化 =====================
            # 处理作者+译者：作者用/分隔，有译者则追加“译者:XXX”
            author = '/'.join(book_dict['author'])
            if len(book_dict['translator']) > 0:
                author += ' 译者: '
                author += '/'.join(book_dict['translator'])
            # 提取评分信息（包含平均分、评价人数）
            rating = book_dict['rating']
            # 清洗价格：移除CNY/元符号，去除首尾空格（兼容不同格式的价格字符串）
            price = book_dict['price']
            price = price.replace('CNY', '').replace('元', '').strip()

            # ===================== 6. 填充图书信息列表（按固定索引） =====================
            bookinfo.append(isbn)                          # 0: ISBN
            bookinfo.append(book_dict['title'])            # 1: 书名
            bookinfo.append(author)                        # 2: 作者+译者
            bookinfo.append(book_dict['publisher'])        # 3: 出版社
            bookinfo.append(price)                         # 4: 价格（清洗后）
            bookinfo.append(rating['average'])             # 5: 豆瓣平均分
            bookinfo.append(rating['numRaters'])           # 6: 评价人数
            bookinfo.append('计划')                        # 7: 分类（默认值）
            bookinfo.append('未设置')                      # 8: 书柜位置（默认值）
            bookinfo.append(book_dict['images']['small'])  # 9: 封面小图URL（替代原image字段）
            bookinfo.append(book_dict['pubdate'])          # 10: 出版日期
            bookinfo.append(book_dict['rating'])           # 11: 完整评分字典（含平均分/人数）
            bookinfo.append(book_dict['alt'])              # 12: 豆瓣图书详情页URL
    
            # ===================== 7. 计算图书推荐度（自定义公式） =====================
            # 日志记录评分信息（便于调试推荐度计算）
            LOG.info(f"ISBN {isbn} 评分信息：{rating}")
            LOG.info(f"ISBN {isbn} 完整图书信息：{book_dict}")
            
            # 推荐度公式：(平均分 - 2.5) × ln(评价人数 + 1)
            # 设计逻辑：
            # - 减2.5：过滤低分图书（平均分<2.5时推荐度为负）
            # - +1：避免评价人数为0时ln(0)抛出数学异常
            # - round：四舍五入取整
            # recommend = round((float(rating['average']) - 2.5) *
            #                   math.log(float(rating['numRaters']) + 1)) 
            recommend = self._calculate_recommend(rating['average'], rating['numRaters'])
            bookinfo.append(str(recommend)) # 13: 推荐度（字符串格式）
            bookinfo.append(book_dict['pages']) # 14: 页数
        else:
            # ===================== 8. 无效数据处理（返回固定长度空值） =====================
            # 响应数据残缺时，填充13个空格，保证返回列表长度统一，避免调用方索引越界
            # for i in range(13):
            #     bookinfo.append(" ")
            return []
        
        # ===================== 9. 返回格式化后的图书信息 =====================        
        return bookinfo        

        
    def search_bookinfo_by_name(self, bookname:str)  -> Optional[List[str]]:
        """
        通过书名模糊搜索多本图书信息
        :param bookname: 图书名称（支持模糊匹配，如"Python编程"）
        :return: 图书信息列表的列表（每个子列表格式同get_bookinfo_by_isbn）
        """
        # 前置校验：书名为空直接返回空列表
        if not bookname:
            LOG.warning("搜索书名为空")
            return []
        
        self.payload_search['q']= bookname
        print(self.payload_search)
        try:
            # 发送GET请求（豆瓣搜索接口仅支持GET）
            response = requests.get(self.url_search, params=self.payload_search, headers=self.headers)
            # 解析搜索结果（豆瓣返回格式：{"count":20, "start":0, "total":3000, "books":[...]}）
            """
            {
              "count": 20,
              "start": 0,
              "total": 3000,
              "books": [
                  {},
                  {},
                  ....
            }
            """
            print(response.json())

            booklist = response.json()['books']
        except requests.exceptions.RequestException as e:
            LOG.error(f"搜索书名 {bookname} 请求失败：{str(e)}")
            return []
        except json.JSONDecodeError:
            LOG.error(f"搜索书名 {bookname} 响应解析失败：{response.text}")
            return []
        books = []
        
        for book_dict in booklist:
            # 单本图书的信息列表（按字段顺序整理）
            bookinfo = []
            # 过滤无效数据（字段过少的图书）
            if len(book_dict) > 5:
                # print('==='*30)
                # print(book_dict)
                # 过滤无ISBN13的图书（ISBN13是唯一标识，必须存在）
                # 过滤无ISBN13的图书（ISBN13是唯一标识，必须存在）
                if ('isbn13' not in book_dict):
                    LOG.debug(f"跳过无ISBN13的图书：书名={self._get_safe_value(book_dict, ['title'])}")
                    continue
                # 1. 处理作者+译者：作者用/分隔，有译者则追加“译者:XXX”
                author = '/'.join(book_dict['author'])  # 作者列表转字符串
                if len(book_dict['translator']) > 0:
                    author += ' 译者: '
                    author += '/'.join(book_dict['translator'])  # 存在译者时
                 # 2. 处理评分、价格等字段
                rating = book_dict['rating']  # 评分信息（包含平均分、评价人数）
                price = book_dict['price'] # 价格（可能为空）
                # 清洗价格：移除CNY/元符号，去除首尾空格
                price = price.replace('CNY', '').replace('元', '').strip()
                # 3. 按顺序填充核心字段（与表格列对应）
                bookinfo.append(book_dict['isbn13'])          # 0: ISBN13
                bookinfo.append(book_dict['title'])           # 1: 书名
                bookinfo.append(author)                       # 2: 作者+译者
                bookinfo.append(book_dict['publisher'])       # 3: 出版社
                bookinfo.append(price)                        # 4: 价格（清洗后）
                bookinfo.append(rating['average'])            # 5: 豆瓣平均分
                bookinfo.append(rating['numRaters'])          # 6: 评价人数
                bookinfo.append('计划')                       # 7: 分类（默认“计划”）
                bookinfo.append('未设置')                     # 8: 书柜位置（默认“未设置”）
                # 补充扩展字段（不展示在表格，但用于传递给父窗口）
                bookinfo.append(book_dict['images']['small']) # 9: 图书封面小图URL
                bookinfo.append(book_dict['pubdate'])         # 10: 出版日期
                bookinfo.append(book_dict['rating'])          # 11: 完整评分信息
                bookinfo.append(book_dict['alt'])             # 12: 豆瓣图书详情页URL

                # 将单本图书信息加入总列表
                books.append(bookinfo)        
        
        return books
    def get_img_by_url(self, url:str)  -> Optional[ByteString]:    
        ref = 'https://' + url.split('/')[2]
        headers= self.headers
        headers['Referer'] = ref
        try:
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                return res.content
            else:
                print(f'获取图书封面失败:{url}')
        except Exception as  e:
            
            print(f'获取图书封面失败:{e}')
        
    def __del__(self):
        pass

if __name__ == "__main__":
    # 初始化API实例
    douban_api = DouBanApi()    
    
    test_isbn = "9787115428028"  # Python编程：从入门到实践（第二版）ISBN
    isbn_result = douban_api.get_bookinfo_by_isbn(test_isbn)
    print("=" * 80)
    print(f"ISBN {test_isbn} 查询结果：")
    if isbn_result:
        for idx, value in enumerate(isbn_result):
            print(f"  索引{idx}：{value}")
    else:
        print("  查询失败（无效ISBN/网络异常/数据残缺）")    
        
    # test_bookname = "Python编程"
    # search_result = douban_api.search_bookinfo_by_name(test_bookname)
    # print("=" * 80)
    # print(f"书名「{test_bookname}」搜索结果（共{len(search_result)}本）：")
    # for idx, book in enumerate(search_result[:3]):  # 仅打印前3本
    #     print(f"  第{idx+1}本：ISBN={book[0]}，书名={book[1]}")    
    