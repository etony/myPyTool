# -*- coding: utf-8 -*-
"""
Created on Mon Feb 14 15:16:03 2022

@author: admin
"""

'''
1、豹子 三张同样大小的牌。x*10*6

2、顺金 花色相同的三张连牌。x*10*5

3、金花 三张花色相同的牌。x*10*4

4、顺子 三张花色不全相同的连牌。x*10*3

5、对子 三张牌中有两张同样大小的牌。x*10*2

6、单张 除以上牌型的牌。 x

'''

import random
import collections
colors = ["♥", "♠", "♦", "♣"]  # 牌色

digi = [str(i) for i in range(2, 11)] + ['J', 'Q', 'K', 'A']  # 点数

n = 5  # 玩家


# 返回项 info = {”牌型":,"分数":}

def getscore(pk_lst):  # 检查大小
    # print(pk_lst,end="  ")
    colors = len(set(pk_color[:1] for pk_color in pk_lst))  # 是否同色
    #print("color:", set(pk_color[:1] for pk_color in pk_lst) )
    lst = list(sc[1:] for sc in pk_lst)  # 转换分值
    for i in range(3):
        if lst[i] == "A":
            lst[i] = 14
        elif lst[i] == "J":
            lst[i] = 11
        elif lst[i] == "Q":
            lst[i] = 12
        elif lst[i] == "K":
            lst[i] = 13
        else:
            lst[i] = int(lst[i])
            
    print(f"分值：{str(lst):<15}", end="      " )

    info = {}
    info['score'] = 0
    if (len(set(lst)) == 1):
        info['type'] = "豹子"
        info['score'] = max(lst)*10**6

    if len(set(lst)) == 2:
        count = collections.Counter(lst)
        for i in count:
            if count[i] == 2:
                info['type'] = "对子"
                info['score'] = i*10**2 + info['score']
            if count[i] == 1:
                info['score'] = i + info['score']
    if len(set(lst)) == 3:
        if max(lst) == min(lst)+2 or set(lst) == {2, 3, 14}:
            info['type'] = "顺子"
            info['score'] = max(lst)*10**3
            if colors == 1:
                info['type'] = "金顺"
                info['score'] = max(lst)*10**5

        else:
            if colors == 1:
                info['type'] = "金花"
                info['score'] = max(lst)*10**4
            else:
                info['type'] = "单张"
                info['score'] = max(lst)

    print(info)
    return info


def get_pk_lst():
    pk = []
    for col in colors:
        for di in digi:
            pk.append(col+di)

    player_list = []
    for i in range(1, n+1):
        player_list.append('熊-'+str(i))

    pk_list = {}

    for i in player_list:
        pk_list[i] = []
        pk_list[i] = (random.sample(pk, 3))
        for p in pk_list[i]:
            pk.remove(p)

    return pk_list


if __name__ == '__main__':

    pk_list = get_pk_lst()

    print("发牌-----")
    result = {}
    for player, pk_lst in pk_list.items():
        print(f'{player:<5}{str(pk_lst):<23}', end="      ")
        info = getscore(pk_list[player])
        result[player] = info['score']
    #print(pk_list)
    print("\n比较-----")

    for key, value in result.items():
        if value == max(result.values()):
            print(key + " 胜 ")
