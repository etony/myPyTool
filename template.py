# -*- coding: utf-8 -*-
"""
创建于  %(date)s

@author: etony.an@gmail.com
"""

import time


# 用于监控程序运行时间
def clock(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print("共耗时: %s秒" % round(end_time - start_time, 2))
        return result

    return wrapper


@clock
def main():
    # do something
    time.sleep(2)
    print("do something.")


if __name__ == '__main__':
    main()
