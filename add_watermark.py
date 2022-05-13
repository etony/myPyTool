# -*- coding: utf-8 -*-
"""
创建于  Fri May 13 11:10:09 2022

@author: etony.an@gmail.com
"""

from watermarker.marker import add_mark
import os

path = ".\\out\\"
if not os.path.exists(path): os.mkdir(path)
add_mark(file=r"banana.jpg", out=r".\out", mark="人生苦短，我用Python。", opacity=0.2, angle=45, space=30)

# file                    图片文件或图片文件夹路径
# mark                    要添加的水印内容
# out                     添加水印后的结果保存位置，默认生成到output文件夹
# color                   水印颜色，默认#8B8B1B
# space                   水印直接的间隔, 默认75个空格
# angle                   水印旋转角度，默认30度
# size                    水印字体的大小，默认50
# opacity                 水印的透明度，默认0.15

# https://pypi.org/project/filestools/