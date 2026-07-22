"""修复玄机小筑开机自启 — 快捷方式→注册表方案
直接运行: python fix_startup.py
或双击:   fix_startup.bat
"""
import os
import sys
import winreg

# ====================== 路径常量 ======================
BASE = os.path.dirname(os.path.abspath(__file__))
LAUNCH_VBS = os.path.join(BASE, 'launch.vbs')

STARTUP_FOLDER = os.path.expandvars(
    r'%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup'
)
LNK_PATH = os.path.join(STARTUP_FOLDER, '玄机小筑.lnk')
REG_KEY = r'Software\Microsoft\Windows\CurrentVersion\Run'
REG_NAME = '玄机小筑'


def main():
    print('=' * 50)
    print('  玄机小筑 - 开机自启修复')
    print('=' * 50)
    print(f'  项目路径: {BASE}')
    print(f'  启动脚本: {LAUNCH_VBS}')
    print()

    # ---- 1. 删除旧的启动快捷方式 ----
    if os.path.exists(LNK_PATH):
        try:
            os.remove(LNK_PATH)
            print('[OK] 已删除旧的启动快捷方式')
        except Exception as e:
            print(f'[WARN] 删除快捷方式失败: {e}')
    else:
        print('[OK] 无旧快捷方式')

    # ---- 2. 写入注册表 Run 键 ----
    # 注册表使用 UTF-16LE，原生支持中文路径，不会乱码
    command = f'wscript.exe //B "{LAUNCH_VBS}"'

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, REG_KEY,
            0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE
        )
    except FileNotFoundError:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_KEY)

    winreg.SetValueEx(key, REG_NAME, 0, winreg.REG_SZ, command)

    # 立即读取验证
    stored_value, _ = winreg.QueryValueEx(key, REG_NAME)
    winreg.CloseKey(key)

    if stored_value == command:
        print('[OK] 注册表 Run 键写入成功')
    else:
        print(f'[FAIL] 写入不匹配!')
        print(f'  预期: {command}')
        print(f'  实际: {stored_value}')
        sys.exit(1)

    # ---- 3. 验证关键文件存在 ----
    all_ok = True
    for f in [LAUNCH_VBS, os.path.join(BASE, 'startup.bat'),
              os.path.join(BASE, 'app.py')]:
        if os.path.exists(f):
            print(f'[OK] {os.path.basename(f)}')
        else:
            print(f'[MISS] {f}')
            all_ok = False

    print()
    if all_ok:
        print('  状态: 正常')
        print('  开机自启将在下次重启后生效。')
        print()
        print('  手动测试命令:')
        print(f'    wscript.exe //B "{LAUNCH_VBS}"')
    else:
        print('  [WARN] 部分文件缺失，请检查!')

    print('=' * 50)
    return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(main())
