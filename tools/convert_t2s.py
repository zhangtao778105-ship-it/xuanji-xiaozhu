# -*- coding: utf-8 -*-
"""一次性脚本：全站繁→简（opencc t2s）+ 修复「色色」叠字

用法：D:/Python314/python.exe tools/convert_t2s.py
转换对象：data/*.json、根目录 *.py、templates/*.html
注意：转换后数据固化为简体，运行时无需 opencc 依赖。
"""

import glob
import os

from opencc import OpenCC

cc = OpenCC('t2s')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def target_files():
    files = []
    files += glob.glob(os.path.join(ROOT, 'data', '*.json'))
    files += glob.glob(os.path.join(ROOT, '*.py'))
    files += glob.glob(os.path.join(ROOT, 'templates', '*.html'))
    files = [f for f in files if os.path.basename(f) != 'convert_t2s.py']
    return sorted(files)


def main():
    files = target_files()
    print('待转换 %d 个文件:' % len(files))
    for f in files:
        print('   ', os.path.relpath(f, ROOT))

    changed = 0
    for f in files:
        with open(f, encoding='utf-8') as fh:
            text = fh.read()
        new = cc.convert(text)
        if '色色' in new:
            new = new.replace('色色', '色')
        if new != text:
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write(new)
            changed += 1
            print('  ✔', os.path.relpath(f, ROOT))
        else:
            print('  -', os.path.relpath(f, ROOT), '(无变化)')
    print('完成，改动 %d 个文件' % changed)


if __name__ == '__main__':
    main()
