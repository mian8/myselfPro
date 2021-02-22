#coding=utf8

"""
常用方法存放处
"""


import time
import requests
import jieba
import difflib

#时间
def getTime(types="s"):
    """
    #时间格式化处理
    :param types:s处理为“秒”结束，d处理为“天”结束
    :return:时间的字符串
    """
    s=time.localtime()
    if types == "s":
        formats='%Y-%m-%d %H:%M:%S'
    elif types == "d":
        formats = '%Y-%m-%d'
    else:formats=""
    result = time.strftime(formats, s)
    return result

#参数整理
def dealData(text,key1="\n",key2=":"):
    """
    将浏览器参数整理为字典输出，内部分组默认以第一个符合条件的字符处理
    :param text: 用三引号输入浏览器负值的参数
    :param key1: 外层分组标识
    :param key2: 内层分组标识
    :return: 字典
    """
    new={}
    dataList=text.split(key1)
    for line in dataList:
        if line.strip() and key2 in line :#排除空行和不符合要求的行
            line=line.split(key2,1)
            try:
                new[line[0]]=line[1].strip()
            except Exception as e:
                print(line,e)
            finally:
                pass
    return new

# 列表拆分方法
def listSpilt(listTemp, n):
    """
    :param listTemp: 被分割列表
    :param n:平分后每份列表的的个数n
    :return:可用list方法直接转化成列表list(listSpilt(range(a,b),c))
    """
    for i in range(0, len(listTemp), n):
        yield listTemp[i:i + n]

# 分词方法，将字符串按照语法拆分为短词
def cutWords(line):
    """
    :param line:字符串
    :return:拆分后的字符串
    """
    line = jieba.cut(line)
    return line

#字符串对比方法
def strRepeatability(s1,s2,other=[]):
    """
    :param s1:字符串1
    :param s2:字符串2
    :param other:需要被排除比较的字符(没卵用)
    :return:比较结果0~1的浮点数
    """
    percnt = difflib.SequenceMatcher(None, s1, s2).quick_ratio()
    return percnt



if __name__ == '__main__':
    text="""searchtime_type: subdate
startTime: 
endTime: 
userid: 959
premisesid:  
pageSize: 10
pageNum: 1"""
    s1="""black轰的一声巨响，烟尘四下掀起，云扬被彻底淹没在烟尘之间。
biquge.com他用手，用脚，用玄气，不管不顾，漫无目的地将"""
    s2="""轰的一声巨响，烟尘四下掀起，云扬被彻底淹没在烟尘之间。
他用手，用脚，用玄气，不管不顾，漫无目的地将"""
    print(strRepeatability(s1,s2))
