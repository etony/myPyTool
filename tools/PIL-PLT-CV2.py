# -*- coding: utf-8 -*-
"""
Created on Tue Nov 15 21:34:28 2022

@author: tony
"""

from PIL import Image
import cv2
import matplotlib.pyplot as plt

import numpy as np

PIL_img = Image.open("rimi.png")
# PIL_img.show()


cv2_img = cv2.imread('rimi.png')
# cv2.imshow('cv2', cv2_img)
# cv2.waitKey()

plt_img = plt.imread('rimi.png')
# plt.imshow(plt_img)
#plt.show()

#PIL 图片
plt.imshow(PIL_img)
plt.imshow(np.array(PIL_img))
cv2.imshow('pil-cv2', cv2.cvtColor(np.asarray(PIL_img), cv2.COLOR_RGB2BGR))
cv2.waitKey()

# cv2 图片
plt.imshow(cv2.cvtColor(np.asarray(cv2_img), cv2.COLOR_RGB2BGR))
Image.fromarray(cv2.cvtColor(np.asarray(cv2_img), cv2.COLOR_RGB2BGR)).show()

# plt 图片
Image.fromarray(np.uint8(plt_img * 255)).show()
Image.fromarray((plt_img * 255).astype(np.uint8)).show()
cv2.imshow('plt-cv2',cv2.cvtColor(np.asarray(plt_img), cv2.COLOR_RGB2BGR))
cv2.waitKey()