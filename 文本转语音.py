# -*- coding: utf-8 -*-
"""
创建于  Mon May  9 08:44:14 2022

@author: etony.an@gmail.com
"""

# from gtts import gTTS
# import os
# tts = gTTS(text="这篇文章主要分享了一个Python处理语音转换库的使用问题，针对该问题给出了具体的解析和代码演示，一共两个方法，帮助粉丝顺利解决了问题。", lang="zh-CN", tld='cn')
# tts.save("hello1.mp3")


# import pyttsx3
# pp = pyttsx3.init()
# pp.say('这篇文章主要分享了一个Python处理语音转换库的使用问题。')
# pp.setProperty('rate',pp.getProperty('rate')+20)
# pp.runAndWait()


# import speech
# speech.say('这篇文章主要分享了一个Python处理语音转换库的使用问题，针对该问题给出了具体的解析和代码演示，一共两个方法，帮助粉丝顺利解决了问题。')


import pyttsx3
tts = pyttsx3.init()

voices = tts.getProperty('voices')
for voice in voices:
    print('id = {} \nname = {} \n'.format(voice.id, voice.name))

# import pyttsx3
# msg = '这篇文章主要分享了一个Python处理语音转换库的使用问题。'
# pp = pyttsx3.init()
# voices = pp.getProperty('voices')
# for v in voices:
#     pp.setProperty('voice', v.id)
#     pp.say(msg)
# pp.runAndWait()

# https://pyttsx3.readthedocs.io/en/latest/engine.html#module-pyttsx3.engine
# getProperty(name : string)
#     rate
#     Integer speech rate in words per minute. Defaults to 200 word per minute.
    
#     voice
#     String identifier of the active voice.
    
#     voices
#     List of pyttsx3.voice.Voice descriptor objects.
    
#     volume
#     Floating point volume in the range of 0.0 to 1.0 inclusive. 