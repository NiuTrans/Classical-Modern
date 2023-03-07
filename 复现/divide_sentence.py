import os
import re
from argparse import ArgumentParser

# 把句子按。！？进行切分（涵盖引号的处理）
def cut_sent(para):
    para = re.sub('\(.*?\)', '', para)
    para = re.sub('（.*?）', '', para)
    para = re.sub('\[.*?\]', '', para)
    para = re.sub('［.*?］', '', para)
    para = re.sub('｛.*?｝', '', para)
    para = re.sub('〖.*?〗', '', para)
    para = re.sub('\{.*?\}', '', para)
    para = re.sub('【.*?】', '', para)
    para = re.sub('〔.*?〕', '', para)
    para = re.sub('『.*?』', '', para)
    para = re.sub('「.*?」', '', para)
    para = re.sub('[〔〕『』「」【】（）\{\}｛｝［\]]', '', para)
    para = re.sub('&lt;', '', para)
    para = re.sub('＝', '', para)
    para = re.sub('\?/font&gt;', '', para)
    para = re.sub('br/&gt;', '', para)
    para = re.sub('&gt;', '', para)
    para = re.sub('<br/><br/>', '', para)
    para = re.sub('yín', '', para)
    para = re.sub('-F', '', para)
    para = re.sub('<br/>', '', para)
    para = re.sub('</strong>', '', para)
    para = re.sub('<strong>', '', para) 
    para = re.sub('', '', para)
    para = re.sub('[a-zA-Z0-9Ａ-ＸХ１／＼$\*②③‖¤àǎň⒃±ьщ〓τ~…＿+#●．§_÷`\.\[\(）\)\-]', '', para)

    para = re.sub('？？。', '。', para)
    para = re.sub("？''", '？”', para)
    para = re.sub('，；', '；', para)
    para = re.sub('。？', '？', para)
    para = re.sub('。，', '，', para)
    para = re.sub('。,', '，', para)
    para = re.sub('？》', '》', para)
    para = re.sub('”,', '”', para)

    para = re.sub('[：][；：、。》,]', '：', para)
    para = re.sub('[；][：；，、。]', '；', para)
    para = re.sub("[，][，！,？\?:：、。!]", '，', para)
    para = re.sub("[。][。\?、'：！!、；]", '。', para)
    para = re.sub("[！][，。、？！]", '！', para)
    para = re.sub("[？][，。、？：；！!\?]", '？', para)
    para = re.sub("[、][，。、？：;；！!\?]", '？', para)

    para = re.sub("！'", '！’', para)
    para = re.sub('？＂', '？”', para)
    para = re.sub('？\'', '？’', para)
    para = re.sub('\?\'', '？’', para)
    para = re.sub('：｀', '：‘', para)
    para = re.sub('：\'', '：‘', para)
    para = re.sub("，'", '，‘', para) 
    para = re.sub("；'", '；‘', para) 
    para = re.sub("、'", '；‘', para) 

    para = re.sub('：，', '，', para)
    para = re.sub('\?、', '、', para)
    para = re.sub("'”", '’', para)
    para = re.sub('\?，', '，', para)

    para = re.sub('—', '一', para)
    para = re.sub('\?\?', '', para)
    para = re.sub('……', '', para)
    para = re.sub('…？', '', para)

    para = re.sub('([。!！？\?][’][”])([^，。、：；！？\?])', r'\1\n\2', para)
    para = re.sub('([。!！？\?])([^”“‘’"])', r"\1\n\2", para)  # 单字符断句符
    para = re.sub('([。!！？\?][”’])([^，。、：；’”！？\?])', r'\1\n\2', para)
    # 如果双引号前有终止符，那么双引号才是句子的终点，把分句符\n放到双引号后，注意前面的几句都小心保留了双引号
    para = re.sub('([。！？\?][”][’])([^，。、：；！？\?])', r'\1\n\2', para)

    # 2023年3月7日更新以下处理
    para = re.sub("[‘’“”']", " ", para)
    para = re.sub('"', " ", para)
    # 更新内容：去除所有引号，并替换成空格，原因：原数据中引号使用无规律，造成了数据质量下降，\
    # 且中英文引号错乱，因此全部采用去除处理，另外因以句子为切割，可能一句话说不全就被截断了，所以 \
    # 去除引号也可使数据更加完整

    para = para.rstrip()  # 段尾如果有多余的\n就去掉它
    return para.split("\n")

def deal_chapter(path, f_log):
    f1 = open(os.path.join(path, 'src.txt'), 'r')
    f2 = open(os.path.join(path, 'tgt.txt'), 'r')
    f3 = open(os.path.join(path, 'temp_ori_sentence.txt'), 'w', buffering=1)
    f4 = open(os.path.join(path, 'temp_trans_sentence.txt'), 'w', buffering=1)

    ori = f1.readlines()
    trans = f2.readlines()

    def Write_sent_to_file(f, l):
        for item in l:
            item = item.strip()
            item = cut_sent(item)
            for i, e in enumerate(item):

                # 分句后若仍有标点开头的句子，是异常句子
                '''
                以下代码为参考代码，对于检测到的异常句子，选择中断并手动修改的方式处理
                if re.match(",!?'，。、；：！？‘’“”", e) :
                    print(item[i-1])
                    print(e)
                    f_log.write(path)
                    print(path)
                    f.close()
                    f_log.close()
                    exit()
                '''
                
                if e:
                    f.write(e+'\n')
    Write_sent_to_file(f3, ori)
    Write_sent_to_file(f4, trans)

    f1.close()
    f2.close()
    f3.close()
    f4.close()

# 遍历数据文件夹
def recursion_dirs(path, f_log):
    files = os.listdir(path)
    if 'src.txt' in files:
        deal_chapter(path, f_log)
    
    for p in files:
        p2 = os.path.join(path, p)
        if os.path.isdir(p2):
            recursion_dirs(p2, f_log)

def main():
    parser = ArgumentParser("divide sentence")
    parser.add_argument("--base_dir", type=str, default="双语数据", required=True)
    args = parser.parse_args()
    base_dir = args.base_dir

    f_log = open("log/cut_sentence_log.txt", 'w', buffering=1)
    recursion_dirs(base_dir, f_log)
    f_log.close()

if __name__ == '__main__':
    main()

