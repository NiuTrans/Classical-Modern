# -*- coding = utf-8 -*-

#爬取网站上的古文

from bs4 import BeautifulSoup
import re
import requests
import time
import os


# 去除一些特殊格式符号
def clear_Data(text):
    # 去除\xa0、\t、\u3000格式的空格
    text = re.sub('\s', '', text)
    return text

# 解析具体章节，并写入文件
def chapter(html, header, dir_name):
    # 只爬原语
    # if os.path.exists(os.path.join(dir_name, "src.txt")):
    #     return 
    # 打开网址
    request = requests.get(url=html, headers=header)
    time.sleep(0.5)
    # 对网址内容构建BS解析对象
    bs = BeautifulSoup(request.text, 'lxml')

    if len(bs.select("body > div.main3 > div.left > div.sons > div > h1")) == 0:
        return
    type2 = str(bs.select("body > div.main3 > div.left > div.sons > div > h1")[0])
    ori = None
    if len(re.findall(":ShowYizhuYuanchuang\(", type2)) > 0 :       # 第一种类型，原文和译文一一对应
        ## 提取目标文字段 ##
        # 提取全部的原文和译文
        id = re.findall('bookv_(.*).aspx', html)[0]
        baseurl = "https://so.gushiwen.cn/guwen/ajaxbfanyiYuanchuang.aspx?id=" + id + "&state=duanyi"
        # 打开网址
        request2 = requests.get(url=baseurl, headers=header)
        time.sleep(0.5)
        # 对网址内容构建BS解析对象
        bs2 = BeautifulSoup(request2.text, 'lxml')
        content = str(bs2.select("body > div.contson")[0])
        ori = re.findall('<p>(.*?)<br\/>', content)
    elif len(re.findall(":ShowYizhu\(", type2)) > 0 :       # 第二种类型，译文段落数更多
        # 原文
        ori = str(bs.select('body > div.main3 > div.left > div > div.cont > div')[0])
        ori = re.findall('<p>(.*?)<\/p>', ori)
    else:   # 没有译文
        content = str(bs.select("#left0 > div.sons > div.cont > div")[0])
        ori = re.findall('<p>(.*?)<\/p>', content)
    
    # 写入文件
    f1 = open(os.path.join(dir_name, "text.txt"), "w")
    for item in ori:
        item = clear_Data(item) + '\n'
        f1.write(item)
    f1.close()

# 解析具体古籍，并按篇章和文章创建文档
def book(baseurl, header, bookName, lastInfo, flog):
    lastSection = lastInfo[1] if isinstance(lastInfo, tuple) else None
    lastChap = lastInfo[2] if isinstance(lastInfo, tuple) else None

    request = requests.get(url=baseurl, headers=header)
    time.sleep(0.5)
    bs = BeautifulSoup(request.text, 'lxml')

    # 提取全部篇章网址id及篇章名
    # 首先统计一共多少个篇章
    chap_num = len(bs.select("body > div.main3 > div.left > div.sons > div"))
    flag = True
    # 收集篇章名及篇章下的文章名（部分书籍没有篇章名，只有文章名）
    for i in range(chap_num):
        chap_detail_list = str(bs.select("body > div.main3 > div.left > div.sons > div")[i])
        t_bookName = bookName
        if chap_num > 1:    # 多篇章书籍
            sectionName = re.findall('<strong>(.*)<\/strong>', chap_detail_list)[0]
            if lastSection is not None and lastSection != "" and lastSection != sectionName and flag:
                continue
            flag = False
            t_bookName = os.path.join(bookName, sectionName)
            if not os.path.exists(t_bookName):
                os.mkdir(t_bookName)
                flog.write('###'+sectionName+'###\n')
                print('    当前篇章：'+sectionName)
        chapID_chapName = dict(zip(re.findall('(https:.*aspx)', chap_detail_list), re.findall('aspx">(.*)<\/a>', chap_detail_list)))
        flag2 = True
        for html, name in chapID_chapName.items():
            if '/' in name:
                name = name.replace('/', '&')
            if lastChap is not None and lastChap != "" and lastChap != name and flag2:
                continue
            flag2 = False
            if not os.path.exists(os.path.join(t_bookName, name)):
                os.mkdir(os.path.join(t_bookName, name))
                flog.write('##'+name+'##\n')
                print('        当前章节：'+name)
            chapter(html, header, os.path.join(t_bookName, name))
            lastChap = None

# 解析具体经部、史部、子部、集部网页下的每本书
def books(baseurl, header, lastInfo, flog, base_dir_name = 'crawl-data'):
    lastBook = lastInfo[0] if isinstance(lastInfo, tuple) else None

    request = requests.get(url=baseurl, headers=header)
    time.sleep(0.5)
    bs = BeautifulSoup(request.text, 'lxml')

    # 提取书链接和书名
    book_list = str(bs.select("body > div.main3 > div.left > div.sons > div")[0])
    book_bookName = dict(zip(re.findall('href="(.*)" target=', book_list), re.findall('_blank">(.*)<\/a>', book_list)))
    flag = True
    for bookurl, bookName in book_bookName.items():
        # lastBook 不为空说明是断点续爬
        if lastBook is not None and bookName != lastBook and flag:
            continue
        flag = False    # 结束断点续爬模式/正常爬取 均是flag = False
        url = "https://so.gushiwen.cn" + bookurl
        dir = os.path.join(base_dir_name, bookName)
        if not os.path.exists(dir):
            os.mkdir(dir)
            flog.write('####'+bookName+'####\n')
            print('当前书籍：' + bookName)
        book(url, header, dir, lastInfo, flog)
        lastInfo, lastBook = None, None

    return True if flag else False  # 该本书没找到上个断点时返回True

def readLog():
    flog = open('log/crawl_src_log.txt', 'r', encoding="utf-8")  
    log = flog.read()

    # 最后一次爬取断点
    lastBOOK, lastSection, lastChap = "", "", ""

    # 读取最后一次爬取时最后一本书籍名称
    if len(re.findall('####(.*)####', log)) > 0:
        lastBOOK = re.findall('####(.*)####', log)[-1] 
    else:
        return None
    
    # 读取最后一次爬取时最后一本书的篇章名称（可能为空）
    BookContent = log[log.find(lastBOOK):]
    if len(re.findall('###(.*)###', BookContent)) > 0:    # 包含篇章
        lastSection = re.findall('###(.*)###', BookContent)[-1]
        BookContent = BookContent[BookContent.find(lastSection):]

    # 读取最后一篇文章
    if len(re.findall('##(.*)##', BookContent)) > 0:   
        lastChap = re.findall('##(.*)##', BookContent)[-1]

    flog.close()
    return lastBOOK, lastSection, lastChap

def main():
    header = {
        "user-agent": "Mozilla/5.0(Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36(KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
    }
    urllist = [
        'https://so.gushiwen.cn/guwen/Default.aspx?p=1&type=%e7%bb%8f%e9%83%a8',
        'https://so.gushiwen.cn/guwen/Default.aspx?p=1&type=%e5%8f%b2%e9%83%a8',
        'https://so.gushiwen.cn/guwen/Default.aspx?p=1&type=%e5%ad%90%e9%83%a8',
        'https://so.gushiwen.cn/guwen/Default.aspx?p=1&type=%e9%9b%86%e9%83%a8'
    ]
    base_dir_name = '古文原文'
    lastInfo = None

    # 创建log文件夹————存储各脚本的日志信息
    if not os.path.exists("log"):
        os.mkdir("log")
    # 爬取脚本日志文件读取
    if os.path.exists('log/crawl_src_log.txt'):
        lastInfo = readLog()
    # 创建爬取单语数据文件夹
    if not os.path.exists(base_dir_name):
        os.mkdir(base_dir_name)
        
    # 爬取日志
    f_log = open('log/crawl_src_log.txt', 'a', buffering=1)
    for url in urllist:
        if not books(url, header, lastInfo, f_log, base_dir_name):
            lastInfo = None
    f_log.close()

if __name__ == '__main__':
    main()