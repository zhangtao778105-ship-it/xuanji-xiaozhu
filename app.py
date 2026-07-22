# -*- coding: utf-8 -*-
"""玄机小筑 — Flask主入口，路由注册，启动逻辑"""

import sys
import io
import os

# 修复 Windows 终端 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import date, datetime

import config
import iching
import guanyin
import daily
import bazi
import liuren
import fengshui
import encyclopedia
import priest

app = Flask(__name__)
app.config['SECRET_KEY'] = 'xuanji-xiaozhu-2026'


# ============================================================
# 首页
# ============================================================
@app.route('/')
def index():
    greeting = priest.greet()
    return render_template('index.html',
                           site_title=config.SITE_TITLE,
                           priest_name=config.PRIEST_NAME,
                           greeting=greeting)


# ============================================================
# 周易金钱卦
# ============================================================
@app.route('/iching')
def iching_page():
    return render_template('iching.html',
                           site_title=config.SITE_TITLE,
                           priest_name=config.PRIEST_NAME)


@app.route('/iching/result', methods=['POST'])
def iching_result():
    # 优先使用前端逐爻投币的结果
    toss_values = []
    for i in range(6):
        v = request.form.get(f'toss_{i}')
        if v is not None:
            toss_values.append(int(v))
    if len(toss_values) == 6:
        result = iching.full_reading_from_values(toss_values)
    else:
        # 表单数据缺失（如直接POST），回退到随机起卦
        result = iching.full_reading()

    interp = result['interpretation']
    orig = interp.get('original', {})

    return render_template('iching_result.html',
                           site_title=config.SITE_TITLE,
                           priest_name=config.PRIEST_NAME,
                           result=result,
                           interpretation=interp,
                           orig=orig)


# API: 单次投币（AJAX）
@app.route('/api/iching/toss')
def api_toss():
    val = iching.toss_once()
    return jsonify({'value': val})


# API: 完整起卦
@app.route('/api/iching/full', methods=['POST'])
def api_iching_full():
    result = iching.full_reading()
    return jsonify(result)


# ============================================================
# 观音灵签
# ============================================================
@app.route('/guanyin')
def guanyin_page():
    return render_template('guanyin.html',
                           site_title=config.SITE_TITLE,
                           priest_name=config.PRIEST_NAME)


@app.route('/guanyin/result', methods=['POST'])
def guanyin_result():
    result = guanyin.full_draw()
    lot = result['lot']
    return render_template('guanyin_result.html',
                           site_title=config.SITE_TITLE,
                           priest_name=config.PRIEST_NAME,
                           result=result,
                           lot=lot)


# ============================================================
# 每日运势
# ============================================================
@app.route('/daily')
def daily_page():
    today = daily._today()
    fortune = daily.daily_fortune(today)
    intro = priest.daily_intro()
    return render_template('daily.html',
                           site_title=config.SITE_TITLE,
                           priest_name=config.PRIEST_NAME,
                           fortune=fortune,
                           intro=intro,
                           today=today)


# ============================================================
# 八字命盘
# ============================================================
@app.route('/bazi')
def bazi_page():
    return render_template('bazi_input.html',
                           site_title=config.SITE_TITLE,
                           priest_name=config.PRIEST_NAME)


@app.route('/bazi/result', methods=['POST'])
def bazi_result():
    try:
        year = int(request.form.get('year', 1990))
        month = int(request.form.get('month', 1))
        day = int(request.form.get('day', 1))
        hour = int(request.form.get('hour', 12))
        gender = request.form.get('gender', '男')

        birth_date = date(year, month, day)
        result = bazi.full_bazi(birth_date, hour, gender)

        return render_template('bazi_result.html',
                               site_title=config.SITE_TITLE,
                               priest_name=config.PRIEST_NAME,
                               result=result,
                               birth_date=birth_date,
                               gender=gender)
    except Exception as e:
        return f"排盘出错：{str(e)}。请检查输入的日期是否有效（支持1900-2100年）。"


# ============================================================
# 大六壬 — 排盘 + 知识库
# ============================================================
@app.route('/liuren')
def liuren_page():
    overview = liuren.get_overview()
    generals = liuren.get_12_generals()
    kejing = liuren.get_kejing()
    bifa = liuren.get_bifa()
    today = date.today()
    return render_template('liuren.html',
                           site_title=config.SITE_TITLE,
                           priest_name=config.PRIEST_NAME,
                           overview=overview,
                           generals=generals,
                           kejing=kejing,
                           bifa=bifa,
                           today=today)


@app.route('/liuren/result', methods=['POST'])
def liuren_result():
    try:
        year = int(request.form.get('year', date.today().year))
        month = int(request.form.get('month', date.today().month))
        day = int(request.form.get('day', date.today().day))
        hour = int(request.form.get('hour', 12))

        birth_date = date(year, month, day)
        pan = liuren.full_pan(birth_date, hour)

        return render_template('liuren_result.html',
                               site_title=config.SITE_TITLE,
                               priest_name=config.PRIEST_NAME,
                               pan=pan,
                               birth_date=birth_date)
    except Exception as e:
        return f"排盘出错：{str(e)}。请检查输入的日期是否有效（支持1900-2100年）。"


# ============================================================
# 风水百科
# ============================================================
@app.route('/fengshui')
def fengshui_page():
    bazhai = fengshui.get_bazhai()
    xuankong = fengshui.get_xuankong()
    xingfa = fengshui.get_xingfa()
    shaqi = fengshui.get_shaqi()
    yiji = fengshui.get_yiji()
    return render_template('fengshui.html',
                           site_title=config.SITE_TITLE,
                           priest_name=config.PRIEST_NAME,
                           bazhai=bazhai,
                           xuankong=xuankong,
                           xingfa=xingfa,
                           shaqi=shaqi,
                           yiji=yiji)


# ============================================================
# 玄学百科
# ============================================================
@app.route('/encyclopedia')
def encyclopedia_page():
    categories = encyclopedia.get_categories()
    return render_template('encyclopedia.html',
                           site_title=config.SITE_TITLE,
                           priest_name=config.PRIEST_NAME,
                           categories=categories)


@app.route('/encyclopedia/<topic>')
def encyclopedia_topic(topic):
    # 尝试作为分类
    cat = encyclopedia.get_category(topic)
    if cat:
        return render_template('search.html',
                               site_title=config.SITE_TITLE,
                               priest_name=config.PRIEST_NAME,
                               topic=topic,
                               content=cat,
                               results=None)

    # 尝试搜索
    results = encyclopedia.search(topic)
    return render_template('search.html',
                           site_title=config.SITE_TITLE,
                           priest_name=config.PRIEST_NAME,
                           topic=topic,
                           content=None,
                           results=results)


# ============================================================
# 搜索API
# ============================================================
@app.route('/search')
def search_page():
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('encyclopedia_page'))

    enc_results = encyclopedia.search(query)
    feng_results = fengshui.search(query)
    liu_results = liuren.search(query)

    all_results = {
        "query": query,
        "encyclopedia": enc_results[:10],
        "fengshui": feng_results[:5],
        "liuren": liu_results[:5],
    }

    return render_template('search.html',
                           site_title=config.SITE_TITLE,
                           priest_name=config.PRIEST_NAME,
                           topic=f"搜索：{query}",
                           content=None,
                           results=all_results,
                           is_search=True)


# ============================================================
# 启动
# ============================================================
def get_local_ip():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


if __name__ == '__main__':
    import qrcode
    from io import BytesIO

    host = config.HOST
    port = config.PORT
    local_ip = get_local_ip()
    url = f"http://{local_ip}:{port}"

    print("=" * 55)
    print(f"  ☯  玄机小筑  ☯")
    print(f"  AI道长占卜 · 本地Web服务")
    print("=" * 55)
    print(f"  局域网地址: {url}")
    print(f"  本地地址:   http://127.0.0.1:{port}")
    print(f"  道长:       {config.PRIEST_NAME}")
    print("=" * 55)

    # 生成终端二维码
    try:
        qr = qrcode.QRCode(version=1, box_size=1, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
    except Exception:
        print("  (二维码生成需要安装 qrcode 库: pip install qrcode)")
        print(f"  请在手机浏览器输入: {url}")
    print()
    print("  按 Ctrl+C 停止服务")
    print("=" * 55)

    app.run(host=host, port=port, debug=config.DEBUG)
