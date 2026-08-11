# -*- coding: utf-8 -*-
"""恢复被 opencc 误转为「干」的八卦「乾」

opencc t2s 词表外的「乾X」（乾位/乾金/乾方/乾宫…）会被误转成「干」。
利用 git 原始版本逐位置对齐：仅当原文是「乾」且转换后是「干」时，
若该处不构成 opencc 已正确转换的合法词（干燥/干旱/干枯…），则恢复为「乾」。
原文本就是「干」的位置不受影响。

用法：D:/Python314/python.exe tools/restore_qian.py
"""

import glob
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# opencc 已正确转换的「乾→干」合法词（原文为乾、简体应为干）
KEEP_DRY = {
    '干燥', '干旱', '干枯', '干草', '干粮', '干涸', '干瘪',
    '干洗', '干练', '干吗', '干戈', '干系', '干杯',
}


def git_head(relpath):
    out = subprocess.run(
        ['git', 'show', 'HEAD:' + relpath.replace(os.sep, '/')],
        capture_output=True, text=True, encoding='utf-8', cwd=ROOT,
    )
    return out.stdout if out.returncode == 0 else None


def target_files():
    files = []
    files += glob.glob(os.path.join(ROOT, 'data', '*.json'))
    files += glob.glob(os.path.join(ROOT, '*.py'))
    files += glob.glob(os.path.join(ROOT, 'templates', '*.html'))
    files = [f for f in files if os.path.basename(f) != 'convert_t2s.py'
             and os.path.basename(f) != 'restore_qian.py']
    return sorted(files)


def restore_file(path):
    rel = os.path.relpath(path, ROOT)
    orig = git_head(rel)
    with open(path, encoding='utf-8') as fh:
        text = fh.read()
    if orig is None:
        return None, '无 git 原始版本'
    if len(orig) != len(text):
        return None, '长度不一致(跳过)，请人工检查'
    chars = list(text)
    restored = 0
    for i, oc in enumerate(orig):
        if oc == '乾' and chars[i] == '干':
            lo = max(0, i - 2)
            hi = min(len(chars), i + 3)
            span = ''.join(chars[lo:hi])
            if not any(k in span for k in KEEP_DRY):
                chars[i] = '乾'
                restored += 1
    new = ''.join(chars)
    if new != text:
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(new)
    return restored, None


def main():
    files = target_files()
    total = 0
    for path in files:
        rel = os.path.relpath(path, ROOT)
        n, err = restore_file(path)
        if err:
            print('  !', rel, err)
            continue
        if n:
            total += n
            print('  ✔', rel, '恢复 %d 处' % n)
    print('共恢复 %d 处「乾」' % total)


if __name__ == '__main__':
    main()
