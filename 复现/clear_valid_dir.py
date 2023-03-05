import os
import shutil
from argparse import ArgumentParser

def rm(path1, f):
    # 返回当前目录下的内容。文件或文件夹
    fls = os.listdir(path1)
    if len(fls)==0:
        f.write(f"删除:{path1}\n")
        os.rmdir(path1)
        return
    elif len(fls) == 1 and fls[0] == '.DS_Store':
        f.write(f"删除:{path1}\n")
        shutil.rmtree(path1)
        return

    for p in fls:
        p2 = os.path.join(path1, p)
        if os.path.isdir(p2):
            rm(p2, f)
            if os.path.exists(p2) and len(os.listdir(p2)) == 0: # 里面删除后这个可能就是空文件了
                f.write(f"删除:{p2}\n")
                os.rmdir(p2) #在这里执行删除
            elif os.path.exists(p2) and len(os.listdir(p2)) == 1 and os.listdir(p2)[0] == '.DS_Store': # mac 文件
                f.write(f"删除:{p2}\n")
                shutil.rmtree(p2)

def main():
    parser = ArgumentParser("delete valid dir")
    parser.add_argument("--base_dir", type=str, default="双语数据", required=True)
    args = parser.parse_args()
    base_dir = args.base_dir

    if not os.path.exists(base_dir):
        print("请提供正确待清空文件夹名称！！！")
    if os.path.exists("log"):
        f = open('log/vlaid_dir_log.txt', 'w')
        rm(base_dir, f)
        f.close()
    else:
        print("需要先创建文件夹'log'!!!")

if __name__ == '__main__':
    main()