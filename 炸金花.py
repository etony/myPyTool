# -*- coding: utf-8 -*-
"""
Created on Mon Feb 14 15:16:03 2022

@author: admin
"""

import random
colors = ["红桃","黑桃","方块","梅花"]

digi =  [str(i) for i in range(2,11)] + ['J','Q','K','A']

pk = []
for i in colors:
    for ii in digi:
        pk.append(i+ii)
print(pk)
print(len(pk))

plalyer = random.sample(pk, 3)

player_list =[]
for i in range(1,5):
    player_list.append('熊'+str(i))
#    player_list['熊'+str(i)] =[]
#    'player'+str(i) = random.sample(pk, 3)
#    for j in 'player'+str(i)

print(player_list)

pk_list={}

for i in player_list:
    pk_list[i]=[]
    pk_list[i]=(random.sample(pk, 3))
    for p in pk_list[i]:
        pk.remove(p)
        
        
print(len(pk))
print(pk_list)        
        
    
