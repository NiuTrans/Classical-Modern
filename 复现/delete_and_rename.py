import os
from argparse import ArgumentParser


def recursion_dir(path):
    files = os.listdir(path)
    if "数据来源.txt" in files:
        if os.path.exists(os.path.join(path, "temp_ori_sentence.txt")):
            os.remove(os.path.join(path, "temp_ori_sentence.txt"))
        if os.path.exists(os.path.join(path, "temp_trans_sentence.txt")):
            os.remove(os.path.join(path, "temp_trans_sentence.txt"))
        if os.path.exists(os.path.join(path, "src.txt")):
            os.remove(os.path.join(path, "src.txt"))
        if os.path.exists(os.path.join(path, "tgt.txt")):
            os.remove(os.path.join(path, "tgt.txt"))

        if os.path.exists(os.path.join(path, "my_trans.txt")):
            os.rename(os.path.join(path, "my_trans.txt"), os.path.join(path, "target.txt"))
        if os.path.exists(os.path.join(path, "my_ori.txt")):
            os.rename(os.path.join(path, "my_ori.txt"), os.path.join(path, "source.txt"))

            f1 = open(os.path.join(path, "source.txt"), "r")
            f2 = open(os.path.join(path, "target.txt"), "r")
            f3 = open(os.path.join(path, "bitext.txt"), "w")
            l1 = f1.readlines()
            l2 = f2.readlines()
            assert len(l1) == len(l2)
            for i in range(len(l1)):
                f3.write("古文：" + l1[i])
                f3.write("现代文：" + l2[i] + '\n\n')
            f1.close()
            f2.close()
            f3.close()
        
    for p in files:
        p2 = os.path.join(path, p)
        if os.path.isdir(p2):
            recursion_dir(p2)



if __name__ == '__main__':
    parser = ArgumentParser("divide sentence")
    parser.add_argument("--base_dir", type=str, default="双语数据", required=True)
    args = parser.parse_args()
    base_dir = args.base_dir

    recursion_dir(base_dir)

