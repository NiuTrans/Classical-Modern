import os
import re
# from numpy import *
# import numpy as np
import math
from tqdm import tqdm
import time
from argparse import ArgumentParser

'''
nohup python -u align.py --base_dir "双语数据"\
 >ans.log 2>&1 &
'''

'''
ps -aux|grep align_first.py
rm -rf 
'''

def clean_sentence(text):
    temp = re.sub('[,.!?;:\'"，。：；‘’“”？！《》 ]', "", text.strip())
    # return set([item for item in temp])
    return temp

def sentence_set(text):
    temp = re.sub('[,.!?;:\'"，。：；‘’“”？！《》 ]', "", text.strip())
    return set([item for item in temp])

# 编辑距离
def minDistance(word1, word2):
    word1 = clean_sentence(word1)
    word2 = clean_sentence(word2)
    n = len(word1)
    m = len(word2)
 
    if n * m == 0:
        return n + m
    
    d = [[0 for i in range(m+1)] for j in range(n+1)]
    for i in range(n+1):
        d[i][0] = i
    for i in range(m+1):
        d[0][i] = i

    for i in range(1, n+1):
        for j in range(1, m+1):
            left = d[i-1][j] + 1
            down = d[i][j-1] + 1
            left_down = d[i-1][j-1]
            if word1[i-1] != word2[j-1]:
                left_down += 1
            d[i][j] = min(left, min(down, left_down)) 
    return d[n][m]

# 代码逻辑和align函数差不多，只不过只计算附近10句的分数情况
def test_score_both(i, j, s, t):
    res = []
    for _ in range(10):

        def update_score(scores, idx, si ,tj):
            scores[idx] = minDistance(si, tj)
            length = max(len(si), len(tj))
            scores[idx] /= length
            changdubi = len(tj) / len(si)
            if changdubi <= 0.95: # 古文长度比译文长度还短很多，被认为是不可能
                scores[idx] += 0.25
            if changdubi > 3.5:
                scores[idx] += 0.25
        
        # scores  11  12  21 
        scores = [100, 100, 100]

        if i+1 != len(s):
            # 21分数   2
            update_score(scores, 2, s[i].strip()+s[i+1], t[j])
        if j+1 != len(t):
            # 12分数    1
            update_score(scores, 1, s[i], t[j].strip()+t[j+1])
        # 11分数     0
        update_score(scores, 0, s[i], t[j])

        mode = scores.index(min(scores)) 

        if mode == 0: # 11
            i += 1
            j += 1
            res.append(min(scores))
        elif mode == 1: # 12
            t[j] = t[j].strip() + t[j+1]
            t.pop(j+1)
        elif mode == 2:
            s[i] = s[i].strip() + s[i+1]
            s.pop(i+1)
        if i == len(s) or j == len(t):
            break
    return res      #, my_ori, my_trans

def test_delete(i, j, addition_length, s, t):
    # 针对第j句译文，计算与之匹配的原文句子下标
    scores = []
    for t_i in range(i, min(i+addition_length, len(s))):
        ssss = test_score_both(t_i, j, s[:], t[:])
        if len(ssss) == 0:
            scores.append(50)
        else:
            scores.append(sum(ssss) / len(ssss))
    j_align_i_number = scores.index(min(scores))
    j_align_i_score = min(scores)

    # 针对第i句原文，计算与之匹配的译文句子下标
    scores = []
    for t_j in range(j, min(j+addition_length, len(t))):
        ssss = test_score_both(i, t_j, s[:], t[:])
        if len(ssss) == 0:
            scores.append(50)
        else:
            scores.append(sum(ssss) / len(ssss))
    i_align_j_number = scores.index(min(scores))
    i_align_j_score = min(scores)

    mode = None
    if abs(j_align_i_score - i_align_j_score) < 0.11:   # 允许的容错分差
        return mode, 0      # 1 ： 1 对齐
    if j_align_i_number != i_align_j_number:
        if j_align_i_score < i_align_j_score:   # 原文多余，需要删除j_align_i_number个句子
            mode = 3
            return mode, j_align_i_number
        else:                                   # 译文多余，需要删除i_align_j_number个句子
            mode = 4
            return mode, i_align_j_number
    else:
        return mode, 0


def align(path):
    temp_ori = os.path.join(path, 'temp_ori_sentence.txt')
    temp_trans = os.path.join(path, 'temp_trans_sentence.txt')
    f_ori = open(temp_ori, 'r', encoding='utf-8')
    f_trans = open(temp_trans, 'r', encoding='utf-8')
    
    s = f_ori.readlines()
    t = f_trans.readlines()
    i, j = 0, 0
    my_ori, my_trans = [], []       # 存储对齐后的原语和译文

    if len(s) == 0 or len(t) == 0:      # 原文或译文为空
        return

    while True:

        def update_score(scores, idx, si ,tj):
            # 归一化编辑距离
            scores[idx] = minDistance(si, tj)
            length = max(len(si), len(tj))
            scores[idx] /= length
            # 长度比
            changdubi = len(tj) / len(si)
            if changdubi <= 0.95: # 古文长度比译文长度还短很多，被认为是不可能
                scores[idx] += 0.25
            if changdubi > 3.5:
                scores[idx] += 0.25

            
        addition_length = abs(len(s) - len(t)) + 10     # 依据原文与译文句子数目差为参考进行辅助对齐
        mode, pop_number = test_delete(i, j, addition_length, s[:], t[:])   # 计算原文第i句与译文第j句是否1:1对齐，若不是，返回i / j应该对齐的下标di / dj

        if mode == 3:        # 原文多余
            for _ in range(pop_number):
                s.pop(i)
            continue
        elif mode == 4:     # 译文多余
            for _ in range(pop_number):
                t.pop(j)
            continue
        
        # scores  1：1   1：2    2：1 
        scores = [100, 100, 100]    # 分数越低被认为越有可能
        if i+1 != len(s):
            # 计算如果是2：1的分数（原文的两句合并后对齐译文的一句话）   idx = 2
            update_score(scores, 2, s[i].strip()+s[i+1], t[j])
        if j+1 != len(t):
            # 计算如果是1：2的分数（原文的一句合并后对齐译文的两句话）   idx = 1
            update_score(scores, 1, s[i], t[j].strip()+t[j+1])
        # 1:1分数     idx = 0
        update_score(scores, 0, s[i], t[j])

        mode = scores.index(min(scores)) 

        if mode == 0: # 1:1
            my_ori.append(s[i])
            my_trans.append(t[j])
            i += 1
            j += 1
        elif mode == 1: # 1：2
            t[j] = t[j].strip() + t[j+1]
            t.pop(j+1)
        elif mode == 2: # 2:1
            s[i] = s[i].strip() + s[i+1]
            s.pop(i+1)
        if i == len(s) or j == len(t):
            break
    
    f_my_ori = open(os.path.join(path, 'my_ori.txt'), 'w', encoding='utf-8')
    f_my_trans = open(os.path.join(path, 'my_trans.txt'), 'w', encoding='utf-8')

    for item in my_ori:
        f_my_ori.write(item)
    for item in my_trans:
        f_my_trans.write(item)

    f_ori.close()
    f_trans.close()
    f_my_ori.close()
    f_my_trans.close()

def recursion_dir(path, res):
    files = os.listdir(path)
    if 'temp_ori_sentence.txt' in files and 'temp_trans_sentence.txt' in files:
        res.append(path)
    
    for p in files:
        p2 = os.path.join(path, p)
        if os.path.isdir(p2):
            recursion_dir(p2, res)

def main():
    parser = ArgumentParser("align sentences")
    parser.add_argument("--base_dir", type=str, default="双语数据", required=True)
    args = parser.parse_args()
    base_dir = args.base_dir

    res = []
    recursion_dir(base_dir, res)
    res.sort(reverse=True)
    bar = tqdm(res)
    for path in bar:
        bar.set_description("{0}".format(path))
        align(path)
        
if __name__ == '__main__':
    main()

