# -*- coding = utf-8 -*-

#爬取网站上的古文

from bs4 import BeautifulSoup
import re
import requests
import time
import os

def write_files(file_name1, file_name2, dic):
    f1 = open(file_name1, "w")
    f2 = open(file_name2, "w")
    for one, two in dic.items():
        one = clear_Data(one) + '\n'
        two = clear_Data(two) + '\n'
        f1.write(one)
        f2.write(two)
    f1.close()
    f2.close()

def write_file(file_name, content, first_line_content = None, type = "0"):
    f = open(file_name, "w")
    if first_line_content:
        f.write(first_line_content)
    if type == "0": # 参考文献
        for i, item in enumerate(content):
            f.write(str(i+1) + "、" + item + "\n")
    elif type == "1":   # 原文/译文
        for item in content:
            item = clear_Data(item) + '\n'
            f.write(item)
    f.close()

# 去除一些特殊格式符号
def clear_Data(text):
    # 去除\xa0、\t、\u3000格式的空格
    text = re.sub('\s', '', text)
    return text

# 解析具体章节，并写入文件
def chapter(html, header, dir_name):
    # 打开网址
    request = requests.get(url=html, headers=header)
    time.sleep(0.5)
    # 对网址内容构建BS解析对象
    bs = BeautifulSoup(request.text, 'lxml')

    if len(bs.select("body > div.main3 > div.left > div.sons > div > h1")) == 0:
        return
    type2 = str(bs.select("body > div.main3 > div.left > div.sons > div > h1")[0])
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
        ori_trans = dict(zip(re.findall('<p>(.*?)<br\/>', content), re.findall('<span style.*?>(.*?)<\/span>', content))) # 原文-译文
        reference_content = str(bs2.select("body > div.cankao")[0]) # 参考文献
        reference_content = re.findall('<span style="line.*?>(.*?)<', reference_content)  # 格式1
        reference_content = reference_content if len(reference_content) > 0 \
                                else re.findall('<span>(.*?)<', str(bs2.select("body > div.cankao")[0]))        # 格式2

        # 写入爬取的段落级双语数据
        write_files(os.path.join(dir_name, "src.txt"), os.path.join(dir_name, "tgt.txt"), ori_trans)
        # 写入参考文献
        write_file(os.path.join(dir_name, "数据来源.txt"), reference_content, first_line_content = "参考资料：\n")
    elif len(re.findall(":ShowYizhu\(", type2)) > 0 :       # 第二种类型，篇章级双语数据
        # 原文
        ori = str(bs.select('body > div.main3 > div.left > div > div.cont > div')[0])
        ori = re.findall('<p>(.*?)<\/p>', ori)

        # 译文
        id = re.findall(":ShowYizhu\((.*?)\,", type2)[0]
        baseurl = "https://so.gushiwen.cn/guwen/ajaxbfanyi.aspx?id=" + id
        request2 = requests.get(url=baseurl, headers=header)
        time.sleep(0.5)
        bs2 = BeautifulSoup(request2.text, 'lxml')
        trans = str(bs2.select('body > div > div.shisoncont > div')[0])
        trans = re.findall('<p>(.*?)<\/p>', trans)

        # 参考文献
        reference_content = str(bs2.select("body > div.sons > div.cankao")[0])
        reference_content = re.findall('<span style="line.*?>(.*?)<', reference_content)
        reference_content = reference_content if len(reference_content) > 0  \
                                else re.findall('<span>(.*?)<', str(bs2.select("body > div.sons > div.cankao")[0]))
        
        # 写入原文-译文
        write_file(os.path.join(dir_name, "src.txt"), ori, type="1")
        write_file(os.path.join(dir_name, "tgt.txt"), ori, type="1")
        # 写入参考文献
        write_file(os.path.join(dir_name, "数据来源.txt"), reference_content, first_line_content = "参考资料：\n")
    else:   # 没有译文，体现为空文件夹，后续会有步骤清空空文件夹
        return

# 解析具体古籍，并按篇章和文章创建文档
def book(baseurl, header, bookName, lastInfo, f_log):
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
                f_log.write('###'+sectionName+'###\n')
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
                f_log.write('##'+name+'##\n')
                print('        当前章节：'+name)
            chapter(html, header, os.path.join(t_bookName, name))
            lastChap = None


# 解析具体经部、史部、子部、集部网页下的每本书
def books(baseurl, header, lastInfo, f_log, base_dir_name = 'crawl-data'):
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
            f_log.write('####'+bookName+'####\n')
            print('当前书籍：' + bookName)
        book(url, header, dir, lastInfo, f_log)
        lastInfo, lastBook = None, None

    return True if flag else False  # 该本书没找到上个断点时返回True

# 读取日志信息
def readLog():
    f_log = open('log/crawl_log.txt', 'r', encoding='utf-8')  
    log = f_log.read()

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

    f_log.close()
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
    base_dir_name = '双语数据'
    lastInfo = None

    # 创建log文件夹————存储各脚本的日志信息
    if not os.path.exists("log"):
        os.mkdir("log")
    # 爬取脚本日志文件读取
    if os.path.exists('log/crawl_log.txt'):
        lastInfo = readLog()
    # 创建爬取双语数据文件夹
    if not os.path.exists(base_dir_name):
        os.mkdir(base_dir_name)
        
    # 爬取日志
    f_log = open('log/crawl_log.txt', 'a', buffering=1)
    for url in urllist:
        if not books(url, header, lastInfo, f_log, base_dir_name):
            lastInfo = None
    f_log.close()

if __name__ == '__main__':
    main()