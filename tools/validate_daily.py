# -*- coding: utf-8 -*-
"""每日运势数据 + 全站简体化校验

断言：
1. yi/ji 无「宜：/忌：」前缀、无「色色」叠字
2. yi 为顿号分隔词组（重写后）
3. hexagrams name_cn 与 daily_fortunes hexagram_name 全集一致
4. _judge_level 覆盖 64 卦
5. 八卦字在 hexagrams / _TRIGRAM_DIR 一致
6. 除「乾」外无繁体残留

用法：D:/Python314/python.exe tools/validate_daily.py
"""

import glob
import json
import os
import re
import sys

from opencc import OpenCC

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

FAIL = 0


def check(name, cond, detail=''):
    global FAIL
    if cond:
        print('  ✓', name)
    else:
        FAIL += 1
        print('  ✗', name, detail)


def main():
    with open('data/hexagrams.json', encoding='utf-8') as f:
        hexagrams = json.load(f)
    with open('data/daily_fortunes.json', encoding='utf-8') as f:
        fortunes = json.load(f)

    print('== 1. yi/ji 语病 ==')
    bad_pre = bad_cc = bad_sep = 0
    for e in fortunes:
        for v in e.get('variants', []):
            yi = v.get('yi', '')
            ji = v.get('ji', '')
            if yi.startswith('宜') or ji.startswith('忌'):
                bad_pre += 1
            if '色色' in yi + ji:
                bad_cc += 1
            if '、' not in yi:
                bad_sep += 1
    check('yi/ji 无「宜：/忌：」前缀', bad_pre == 0, 'bad=%d' % bad_pre)
    check('yi/ji 无「色色」', bad_cc == 0, 'bad=%d' % bad_cc)
    check('yi 含「、」分隔', bad_sep == 0, 'bad=%d' % bad_sep)

    print('== 2. 卦名一致 ==')
    hex_names = set(v['name_cn'] for v in hexagrams.values())
    fort_names = set(e['hexagram_name'] for e in fortunes)
    check('64 卦全集一致', hex_names == fort_names,
          'diff=%s' % (hex_names ^ fort_names))

    print('== 3. 等级判定覆盖 ==')
    import daily
    daily._load()
    miss = [n for n in hex_names if not daily._judge_level(n)]
    check('_judge_level 全覆盖', not miss, str(miss))

    print('== 4. 八卦字一致 ==')
    trig_hex = set()
    for v in hexagrams.values():
        trig_hex.add(v['upper_trigram'])
        trig_hex.add(v['lower_trigram'])
    trig_dir = set(daily._TRIGRAM_DIR.keys())
    check('八卦字一致', trig_hex == trig_dir, '%s vs %s' % (trig_hex, trig_dir))

    print('== 5. 繁体残留（除乾） ==')
    cc = OpenCC('t2s')
    bad = {}
    for f in glob.glob('data/*.json') + glob.glob('*.py') + glob.glob('templates/*.html'):
        if f.startswith('tools'):
            continue
        txt = open(f, encoding='utf-8').read()
        conv = cc.convert(txt)
        if conv != txt:
            ch = {a for a, b in zip(txt, conv) if a != b} - {'乾'}
            if ch:
                bad[f] = ch
    check('无繁体残留', not bad, str(bad))

    print()
    print('结果:', '全部通过 ✓' if FAIL == 0 else '%d 项失败 ✗' % FAIL)
    sys.exit(1 if FAIL else 0)


if __name__ == '__main__':
    main()
