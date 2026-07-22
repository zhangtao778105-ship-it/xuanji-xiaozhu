# -*- coding: utf-8 -*-
"""八字命盘引擎 — 四柱推算、十神、五行、纳音、大运、神煞"""

import hashlib
from datetime import date
from utils import (
    load_json, solar_to_lunar, TIANGAN, DIZHI,
    JIEQI_APPROX,
)

_BAZI = None


def _deterministic_pick(pool, *seed_parts):
    """同一输入永远选同一条，不同输入几乎不可能碰撞"""
    if not pool:
        return ""
    seed = "|".join(str(s) for s in seed_parts)
    h = hashlib.md5(seed.encode())
    idx = int.from_bytes(h.digest()[:4], 'big') % len(pool)
    return pool[idx]


def _pick_n(pool, n, *seed_parts):
    """从池中确定性选取 n 条不重复的条目"""
    if not pool:
        return []
    n = min(n, len(pool))
    result = []
    for i in range(n):
        idx = int.from_bytes(hashlib.md5(f"{'|'.join(str(s) for s in seed_parts)}|pick{i}".encode()).digest()[:4], 'big') % len(pool)
        # 避免重复，线性探测
        attempts = 0
        while pool[idx] in result and attempts < len(pool):
            idx = (idx + 1) % len(pool)
            attempts += 1
        result.append(pool[idx])
    return result


def _load():
    global _BAZI
    if _BAZI is None:
        _BAZI = load_json('bazi_data.json')


# ============================================================
# 1. 年柱 — 以立春为界
# ============================================================
def calc_year_pillar(d):
    """计算年柱干支索引"""
    year = d.year
    # 立春在2月4日附近
    if d.month < 2 or (d.month == 2 and d.day < 4):
        year -= 1
    # 年干年支以立春为界
    # 1864年为甲子年(0)
    base_year = 1864
    idx = (year - base_year) % 60
    return idx  # 0-59在60甲子中的位置


def year_ganzhi_str(idx):
    """年柱索引转干支字符串"""
    return TIANGAN[idx % 10] + DIZHI[idx % 12]


# ============================================================
# 2. 月柱 — 以节气为界，五虎遁年起月法
# ============================================================
def get_month_branch(d):
    """根据日期确定月支（以节气为界）"""
    for i, (name, m, day) in enumerate(JIEQI_APPROX):
        if name == "立春":
            continue  # 立春是年柱的分界
        jieqi_date = date(d.year, m, day)
        if d < jieqi_date:
            # 属于前一个月
            return DIZHI[(i + 1) % 12]
    # 12月（大雪到小寒之间，或小寒之后新一年开始前）
    # 小寒之后属丑月
    xiaohan = date(d.year, 1, 6)
    if d >= xiaohan:
        return "丑"
    return "子"


def calc_month_pillar(year_gz_idx, d):
    """五虎遁年起月法计算月柱"""
    year_gan = TIANGAN[year_gz_idx % 10]

    # 五虎遁：甲己之年丙作首，乙庚之年戊为头，丙辛之年寻庚上，丁壬壬寅顺水流，戊癸之年甲寅求
    month_gan_start = {
        "甲": "丙", "己": "丙",
        "乙": "戊", "庚": "戊",
        "丙": "庚", "辛": "庚",
        "丁": "壬", "壬": "壬",
        "戊": "甲", "癸": "甲",
    }

    # 月份对应地支：正月寅(2), 二月卯(3), ..., 十二月丑(1)
    # 以节气为界
    month_zhi = get_month_branch(d)
    month_zhi_idx = DIZHI.index(month_zhi)

    start_gan = month_gan_start[year_gan]
    start_gan_idx = TIANGAN.index(start_gan)

    # 寅月=正月 → start_gan_idx+0
    # month_zhi_idx=2(寅)时，offset=0；month_zhi_idx=3(卯)时，offset=1
    offset = (month_zhi_idx - 2) % 12

    month_gan = TIANGAN[(start_gan_idx + offset) % 10]
    return month_gan + month_zhi


# ============================================================
# 3. 日柱 — 基于1900-01-01甲戌日的累积天数法
# ============================================================
def calc_day_pillar(d):
    """计算日柱（甲戌日为基准）"""
    base = date(1900, 1, 1)
    base_gz = 10  # 甲戌在60甲子中的索引（0-based）
    days_diff = (d - base).days
    gz_idx = (base_gz + days_diff) % 60
    return TIANGAN[gz_idx % 10] + DIZHI[gz_idx % 12], gz_idx


# ============================================================
# 4. 时柱 — 五鼠遁日起时法
# ============================================================
def calc_hour_pillar(day_gan, hour):
    """五鼠遁日起时法计算时柱"""
    # 时辰：子时23-1, 丑1-3, ..., 亥21-23
    hour_zhi_idx = (hour + 1) // 2 % 12
    hour_zhi = DIZHI[hour_zhi_idx]

    # 五鼠遁：甲己还加甲，乙庚丙作初，丙辛从戊起，丁壬庚子居，戊癸何方发，壬子是真途
    hour_gan_start = {
        "甲": "甲", "己": "甲",
        "乙": "丙", "庚": "丙",
        "丙": "戊", "辛": "戊",
        "丁": "庚", "壬": "庚",
        "戊": "壬", "癸": "壬",
    }

    start_gan = hour_gan_start[day_gan]
    start_gan_idx = TIANGAN.index(start_gan)
    hour_gan = TIANGAN[(start_gan_idx + hour_zhi_idx) % 10]

    return hour_gan + hour_zhi


# ============================================================
# 5. 十神计算
# ============================================================
def calc_shishen(day_gan, pillar_gan):
    """根据日干和柱干计算十神"""
    _load()
    wuxing_map = _BAZI["wuxing_map"]
    sheng = _BAZI["wuxing_sheng"]
    ke = _BAZI["wuxing_ke"]
    yin_yang = _BAZI["yin_yang"]

    dwx = wuxing_map.get(day_gan, "")
    pwx = wuxing_map.get(pillar_gan, "")
    dy = yin_yang.get(day_gan, "")
    py = yin_yang.get(pillar_gan, "")

    if dwx == pwx:
        return "比肩" if dy == py else "劫财"

    # 我生
    if sheng.get(dwx) == pwx:
        return "食神" if dy == py else "伤官"

    # 我克
    if ke.get(dwx) == pwx:
        return "偏财" if dy == py else "正财"

    # 克我
    if ke.get(pwx) == dwx:
        return "七杀" if dy == py else "正官"

    # 生我
    if sheng.get(pwx) == dwx:
        return "偏印" if dy == py else "正印"

    return "?"


# ============================================================
# 6. 纳音
# ============================================================
def calc_nayin(gz_str):
    """根据干支获取纳音"""
    _load()
    g = TIANGAN.index(gz_str[0])
    z = DIZHI.index(gz_str[1])
    idx = (g * 6 + z) % 60 // 2
    return _BAZI["nayin"][idx % 30] if _BAZI["nayin"] else ""


# ============================================================
# 7. 神煞
# ============================================================
def calc_shensha(day_gan, day_zhi, year_zhi, month_zhi):
    """计算主要神煞"""
    _load()
    shensha_data = _BAZI.get("shensha", {})
    result = {}

    # 天乙贵人
    tianyi_map = shensha_data.get("天乙贵人", {})
    for key, vals in tianyi_map.items():
        if day_gan in key:
            result["天乙贵人"] = vals
            break

    # 文昌
    wenchang = shensha_data.get("文昌", {})
    if day_gan in wenchang:
        result["文昌"] = wenchang[day_gan]

    # 驿马（以年支或日支看）
    yima_map = shensha_data.get("驿马", {})
    for sanhe, ma in yima_map.items():
        if year_zhi in sanhe:
            result["驿马"] = ma
            break

    # 桃花
    taohua_map = shensha_data.get("桃花", {})
    for sanhe, hua in taohua_map.items():
        if year_zhi in sanhe:
            result["桃花"] = hua
            break

    # 羊刃
    yangren = shensha_data.get("羊刃", {})
    if day_gan in yangren:
        result["羊刃"] = yangren[day_gan]

    # 空亡
    kongwang = shensha_data.get("空亡", {})
    xun = TIANGAN[(TIANGAN.index(day_gan) // 5) * 5] + DIZHI[(DIZHI.index(day_zhi) // 6) * 6]
    for xun_key, kw in kongwang.items():
        if xun_key[:2] == xun[:2]:
            result["空亡"] = kw
            break

    return result


# ============================================================
# 8. 大运
# ============================================================
def calc_dayun(year_gz_str, gender, d):
    """计算大运排盘
    gender: '男' or '女'
    """
    year_gan = year_gz_str[0]
    year_zhi = year_gz_str[1]
    yin_yang = _load() or {}
    _load()
    yy = _BAZI["yin_yang"]

    is_yang = yy.get(year_gan) == "阳"

    # 阳男阴女顺排，阴男阳女逆排
    if (is_yang and gender == "男") or (not is_yang and gender == "女"):
        direction = "顺"
    else:
        direction = "逆"

    # 起运岁数：从出生日到下一个/上一个节气的天数÷3
    # 简化计算
    birth_month = d.month
    birth_day = d.day

    # 查找出生在哪个节气区间
    qiyun_age = 0
    for i, (name, m, day) in enumerate(JIEQI_APPROX):
        jieqi_date = date(d.year, m, day)
        if d >= jieqi_date:
            continue
        # 下一个节气
        if direction == "顺":
            days_to_jieqi = (jieqi_date - d).days
            qiyun_age = max(1, round(days_to_jieqi / 3))
        break
    else:
        # 出生在最后一个节气之后
        next_jieqi = date(d.year + 1, JIEQI_APPROX[0][1], JIEQI_APPROX[0][2])
        if direction == "顺":
            days_to_jieqi = (next_jieqi - d).days
            qiyun_age = max(1, round(days_to_jieqi / 3))

    if direction == "逆":
        for i in range(len(JIEQI_APPROX) - 1, -1, -1):
            name, m, day = JIEQI_APPROX[i]
            jieqi_date = date(d.year, m, day)
            if d <= jieqi_date:
                continue
            days_from_jieqi = (d - jieqi_date).days
            qiyun_age = max(1, round(days_from_jieqi / 3))
            break

    # 排大运：从月柱开始顺或逆排
    month_zhi = get_month_branch(d)
    month_zhi_idx = DIZHI.index(month_zhi)
    month_gan = calc_month_pillar(TIANGAN.index(year_gan), d)[0]
    month_gan_idx = TIANGAN.index(month_gan)

    dayun_list = []
    for i in range(8):  # 排8步大运
        if direction == "顺":
            gan_idx = (month_gan_idx + i + 1) % 10
            zhi_idx = (month_zhi_idx + i + 1) % 12
        else:
            gan_idx = (month_gan_idx - i - 1) % 10
            zhi_idx = (month_zhi_idx - i - 1) % 12

        age_start = qiyun_age + i * 10
        dayun_list.append({
            "age": f"{age_start}-{age_start+9}岁",
            "ganzhi": TIANGAN[gan_idx] + DIZHI[zhi_idx],
            "nayin": calc_nayin(TIANGAN[gan_idx] + DIZHI[zhi_idx]),
        })

    return {
        "direction": "顺排" if direction == "顺" else "逆排",
        "qiyun_age": qiyun_age,
        "dayun": dayun_list,
    }


# ============================================================
# 9. 五行统计
# ============================================================
def count_wuxing(pillars):
    """统计四柱中的五行数量"""
    _load()
    wuxing_map = _BAZI["wuxing_map"]
    counts = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    for p in pillars:
        gz = p["ganzhi"]
        for ch in gz:
            wx = wuxing_map.get(ch, "")
            if wx in counts:
                counts[wx] += 1
    return counts


# ============================================================
# 10. 用神建议（简化规则）
# ============================================================
def analyze_yongshen(pillars, wuxing_counts, day_gan):
    """简化用神分析"""
    _load()
    wuxing_map = _BAZI["wuxing_map"]
    dwx = wuxing_map.get(day_gan, "")
    sheng_map = _BAZI["wuxing_sheng"]
    ke_map = _BAZI["wuxing_ke"]

    # 日主五行
    ri_wx = dwx

    # 生我者 = 印
    sheng_wo = [k for k, v in sheng_map.items() if v == ri_wx]

    # 我生者 = 食伤
    wo_sheng = sheng_map.get(ri_wx, "")

    # 克我者 = 官杀
    ke_wo = [k for k, v in ke_map.items() if v == ri_wx]

    # 我克者 = 财
    wo_ke = ke_map.get(ri_wx, "")

    # 判断身强身弱
    ri_count = wuxing_counts.get(ri_wx, 0)
    sheng_count = sum(wuxing_counts.get(w, 0) for w in sheng_wo)

    if ri_count + sheng_count >= 5:
        body = "身强"
        # 身强喜克泄耗
        yongshen = [wo_ke, wo_sheng] + ke_wo
        yongshen = [w for w in yongshen if w]
    else:
        body = "身弱"
        # 身弱喜生扶
        yongshen = sheng_wo + [ri_wx]

    return {
        "body_type": body,
        "day_master_wuxing": ri_wx,
        "yongshen": yongshen[:3],
        "advice": f"日主{ri_wx}{body}，宜补{'、'.join(yongshen[:3])}之气。",
    }


# ============================================================
# 11. 完整排盘
# ============================================================
def full_bazi(birth_date, birth_hour, gender="男"):
    """
    完整八字排盘
    birth_date: date对象
    birth_hour: 整数, 0-23
    gender: '男' 或 '女'
    """
    _load()

    # 年柱
    year_gz_idx = calc_year_pillar(birth_date)
    year_gz = year_ganzhi_str(year_gz_idx)
    year_gan = year_gz[0]
    year_zhi = year_gz[1]

    # 月柱
    month_gz = calc_month_pillar(year_gz_idx, birth_date)

    # 日柱
    day_gz, day_gz_idx = calc_day_pillar(birth_date)
    day_gan = day_gz[0]
    day_zhi = day_gz[1]

    # 时柱
    hour_gz = calc_hour_pillar(day_gan, birth_hour)

    # 生肖
    shengxiao = _BAZI["shengxiao"][DIZHI.index(year_zhi)]

    # 各柱详情
    pillars = [
        {"name": "年柱", "ganzhi": year_gz, "nayin": calc_nayin(year_gz),
         "canggan": _BAZI.get("地支藏干", {}).get(year_zhi, []),
         "shishen": calc_shishen(day_gan, year_gan)},
        {"name": "月柱", "ganzhi": month_gz, "nayin": calc_nayin(month_gz),
         "canggan": _BAZI.get("地支藏干", {}).get(month_gz[1], []),
         "shishen": calc_shishen(day_gan, month_gz[0])},
        {"name": "日柱", "ganzhi": day_gz, "nayin": calc_nayin(day_gz),
         "canggan": _BAZI.get("地支藏干", {}).get(day_zhi, []),
         "shishen": "日主"},
        {"name": "时柱", "ganzhi": hour_gz, "nayin": calc_nayin(hour_gz),
         "canggan": _BAZI.get("地支藏干", {}).get(hour_gz[1], []),
         "shishen": calc_shishen(day_gan, hour_gz[0])},
    ]

    # 五行统计
    wx_counts = count_wuxing(pillars)

    # 神煞
    shensha = calc_shensha(day_gan, day_zhi, year_zhi, month_gz[1])

    # 大运
    dayun = calc_dayun(year_gz, gender, birth_date)

    # 用神
    yongshen = analyze_yongshen(pillars, wx_counts, day_gan)

    # 农历日期
    try:
        lunar_year, lunar_month, lunar_day, is_leap = solar_to_lunar(birth_date)
    except Exception:
        lunar_year, lunar_month, lunar_day, is_leap = birth_date.year, birth_date.month, birth_date.day, False

    # 详细分析（确定性叙事流）
    analysis = generate_analysis(pillars, wx_counts, yongshen, shensha, dayun, gender, shengxiao, day_gan, day_zhi, birth_date, birth_hour)

    # AI 深度详解（可插拔）
    try:
        from ai_interpreter import get_interpreter
        ai = get_interpreter()
        if ai.enabled:
            ai_data = {
                "gender": gender,
                "shengxiao": shengxiao,
                "pillars": pillars,
                "wuxing_counts": wx_counts,
                "yongshen": yongshen,
                "shensha": shensha,
                "dayun": dayun,
                "day_gan": day_gan,
                "day_zhi": day_zhi,
                "lunar_date": f"{'闰' if is_leap else ''}{lunar_month}月{lunar_day}日",
            }
            ai_text = ai.interpret("bazi", ai_data)
            if ai_text:
                analysis += f"\n\n【凤年真人深度详解】\n{ai_text}"
    except Exception:
        pass  # AI 不可用时静默降级

    return {
        "birth_date": birth_date.isoformat(),
        "birth_hour": birth_hour,
        "gender": gender,
        "lunar_date": f"{'闰' if is_leap else ''}{lunar_month}月{lunar_day}日",
        "shengxiao": shengxiao,
        "pillars": pillars,
        "wuxing_counts": wx_counts,
        "shensha": shensha,
        "dayun": dayun,
        "yongshen": yongshen,
        "analysis": analysis,
    }


# ============================================================
# 12. 白话详细分析（200+字）
# ============================================================
def generate_analysis(pillars, wx_counts, yongshen, shensha, dayun, gender, shengxiao, day_gan, day_zhi, birth_date=None, birth_hour=None):
    """生成详细的命盘白话分析（确定性输出，叙事流风格）"""
    _load()

    # ── 特殊日期：硬编码手写解读 ──
    if birth_date is not None and birth_hour is not None:
        special_key = (birth_date.isoformat(), gender, birth_hour)
    else:
        special_key = None

    if special_key in SPECIAL_READINGS:
        return SPECIAL_READINGS[special_key]

    wuxing_map = _BAZI["wuxing_map"]
    dwx = yongshen["day_master_wuxing"]
    body = yongshen["body_type"]
    ys = "、".join(yongshen["yongshen"])
    yongshen_first = yongshen["yongshen"][0] if yongshen["yongshen"] else dwx

    # 五行排序
    wx_list = [(k, v) for k, v in wx_counts.items()]
    wx_list.sort(key=lambda x: -x[1])
    most_wx = wx_list[0]
    least_wx = wx_list[-1]

    # 十神列表
    shishen_list = [p["shishen"] for p in pillars if p["shishen"] != "日主"]
    shishen_str = "、".join(shishen_list)

    # 四柱干支用于种子
    year_gz = pillars[0]["ganzhi"]
    month_gz = pillars[1]["ganzhi"]
    day_gz = pillars[2]["ganzhi"]
    hour_gz = pillars[3]["ganzhi"]
    year_zhi = year_gz[1]
    month_zhi = month_gz[1]
    hour_zhi = hour_gz[1]

    # ── 构建各部分（全部确定性 hash 选取）──

    # 开场白
    opening = _deterministic_pick(
        _BAZI.get("opening_lines", [""]),
        day_gan, gender, year_zhi
    )

    # 日主性格
    daymaster_pool = _BAZI.get("daymaster_profiles", {}).get(day_gan, [])
    char_desc = _deterministic_pick(daymaster_pool, day_gan, day_zhi, gender)
    if not char_desc:
        wx_char = {
            "木": "仁慈善良，有恻隐之心，志向高远，如大树般正直向上。但有时过于耿直，不擅变通。",
            "火": "热情奔放，积极向上，有领导才能和感染力。但有时急躁冲动，缺乏耐心。",
            "土": "诚信敦厚，稳重踏实，包容万物。但有时过于保守，缺乏灵活性。",
            "金": "刚毅果断，讲义气，是非分明。但有时过于刚硬，容易得罪人。",
            "水": "聪明灵活，善于变通，足智多谋。但有时心思太活，容易三心二意。",
        }
        char_desc = wx_char.get(dwx, "性格平和。")

    # 十神组合检测
    shishen_combos_pool = _BAZI.get("shishen_combos", {})
    detected_combos = []
    if "食神" in shishen_str and ("正财" in shishen_str or "偏财" in shishen_str):
        detected_combos.append("食神生财")
    if "伤官" in shishen_str and "正官" in shishen_str:
        detected_combos.append("伤官见官")
    if ("正官" in shishen_str or "七杀" in shishen_str) and ("正印" in shishen_str or "偏印" in shishen_str):
        detected_combos.append("官印相生")
    if ("比肩" in shishen_str or "劫财" in shishen_str) and ("正财" in shishen_str or "偏财" in shishen_str):
        detected_combos.append("比劫夺财")
    if ("食神" in shishen_str or "伤官" in shishen_str) and not ("正财" in shishen_str or "偏财" in shishen_str):
        detected_combos.append("食伤泄秀")
    if ("正财" in shishen_str or "偏财" in shishen_str) and ("正官" in shishen_str or "七杀" in shishen_str):
        detected_combos.append("财官双美")
    if ("正印" in shishen_str or "偏印" in shishen_str):
        detected_combos.append("印星护身")

    combo_text = ""
    if detected_combos:
        combo = _deterministic_pick(detected_combos, day_gan, day_zhi, month_zhi, "combo")
        combo_pool = shishen_combos_pool.get(combo, [])
        combo_text = _deterministic_pick(combo_pool, combo, month_zhi, year_zhi, gender)

    # 格局分析（身强/身弱叙事）
    body_pool = _BAZI.get("body_narratives", {}).get(body, [])
    body_text = _deterministic_pick(body_pool, body, day_gan, most_wx[0], gender)

    # 神煞（融入叙事，不单独标注标题）
    shensha_pool = _BAZI.get("shensha_interpretations", {})
    shensha_texts = []
    for name, val in shensha.items():
        pool = shensha_pool.get(name, [])
        if pool:
            t = _deterministic_pick(pool, name, day_gan, day_zhi, year_zhi, hour_zhi)
        else:
            t = ""
        if t:
            shensha_texts.append(t)

    # 健康养生
    health_pool = _BAZI.get("health_tips", {}).get(least_wx[0], [])
    health_text = _deterministic_pick(health_pool, least_wx[0], day_zhi, gender)

    # 行业方向
    career_pool = _BAZI.get("career_directions", {}).get(yongshen_first, [])
    if not career_pool:
        # fallback: 找一个非空的用神五行
        for ys_elem in yongshen["yongshen"]:
            career_pool = _BAZI.get("career_directions", {}).get(ys_elem, [])
            if career_pool:
                break
    career_text = _deterministic_pick(career_pool, yongshen_first, day_gan, gender)

    # 结语：从 conclusion_parts 中选取 2-3 条拼接
    conclusion_pool = _BAZI.get("conclusion_parts", [])
    conclusion_picks = _pick_n(conclusion_pool, 3, day_gan, day_zhi, body, gender, "conclusion")
    conclusion_text = "".join(conclusion_picks)

    # 大运提示
    dayun_tip = ""
    if dayun["dayun"]:
        first_dayun = dayun["dayun"][0]
        dayun_tip = f"起运{dayun['qiyun_age']}岁，{dayun['direction']}。首步大运{first_dayun['ganzhi']}（{first_dayun['nayin']}），行{first_dayun['age']}岁。大运十年一换逢交运之年宜多加注意。"

    # ── 组装叙事流（无【】标题）──
    parts = [opening]
    parts.append("")

    # 日主性格 + 十神 + 格局 融为一体
    parts.append(char_desc)
    if combo_text:
        parts.append("")
        parts.append(combo_text)
    if body_text:
        parts.append("")
        parts.append(body_text)

    # 神煞融入
    if shensha_texts:
        parts.append("")
        parts.append(" ".join(shensha_texts))

    # 大运
    if dayun_tip:
        parts.append("")
        parts.append(dayun_tip)

    # 健康 + 行业
    if health_text:
        parts.append("")
        parts.append(health_text)
    if career_text:
        parts.append("")
        parts.append(career_text)

    # 结语
    if conclusion_text:
        parts.append("")
        parts.append(conclusion_text)

    return "\n".join(parts)


# ── 特殊日期手写解读 ──
SPECIAL_READINGS = {
    ("2005-07-12", "男", 12): """这副八字，乙酉 癸未 丁酉 丙午，属鸡。排完之后又多看了两眼。

丁火是你的日主，生在未月正是盛夏。天干上癸水七杀透出，丙火劫财在时柱帮身。你这个人表面温和内里却有股不服软的劲——丁火不是丙火那种大火，是烛火，不刺眼但灭不掉。

地支双酉金当财星，你天生对钱有感觉。但酉酉自刑，有时候会自己跟自己较劲——明明想通了的事到了半夜又来一轮。你的脑子太活了，这是天赋也是负担。

五行上，火有三个、金有两个、水一个、木一个、土一个。火偏旺而金水也有根基，格局不算差。但日主丁火在这局里其实是偏弱的——七杀癸水当头，财星酉金在下面耗着你。所以你虽然心里主意正但遇事容易想太多。需要木火来扶你一把。

好消息是天乙贵人在你的日柱和时柱上坐着。酉是天乙贵人的位置，你一生关键时刻总有人拉一把。文昌也坐在酉上，读书考试有老天爷赏的聪明劲，但用不用得看你自己。

未月出生的人包容心强，能容人。你做朋友应该挺好——不斤斤计较不小肚鸡肠。但也可能因为太好说话被人占便宜。这一点要自己留个心眼。

你这八字适合做什么？丁火喜木火，文化教育传媒创意类的都行。你骨子里是个聪明人，学什么都快。但也因为学得快容易三分钟热度。选定一个方向沉下去做五年你会感谢现在的自己。

大运方面，起运后头一两步走得不会太快，打好基础比较重要。三十岁之后运势会有明显提升。

命途不是一条直线。你有贵人运有文昌运有灵活的脑子，底子不差。关键是把聪明劲用在正地方别折腾自己。别人还没打败你你自己先把自己耗光了——别做这种事。""",

    ("2005-02-12", "女", 8): """八字排定。乙酉 戊寅 丁卯 甲辰，属鸡。

这副八字排完之后最显眼的就是——木太多了。寅卯辰三会东方木局，印星甲木透在时柱，乙木坐在年干。满盘木气。你是丁火日主，木生火，所以火虽然本体不多但有整个森林给你添柴。你的生命力很旺盛，精神头比别人足。

戊土伤官坐在寅月透出来，代表你是个有才华且愿意表达的人。伤官的人不喜欢被压抑——想到什么就说什么，有情绪就流露出来。这在创意艺术类的领域是很大的优势。但伤官也让你有时候说话太直，容易得罪人而不自知。这份直率是你的魅力也是你的课题。

日柱丁卯，丁火坐卯木偏印。偏印生身说明你的直觉很准，心思细腻，有时候想得太多甚至会预判别人的预判。这份敏锐让你在人际关系中少踩很多坑但也可能让你活得太累。放松一点世界没那么多阴谋。

你的五行分布很极端——木占了四个、火一个、土一个、金一个、水零。五行缺水是这副命盘最需要注意的。水是你的官杀也是调候。缺水意味着你有时候会缺乏一种清醒的自我约束——对人对事可能太过投入而忘了停一下。学一学水的智慧：该流就流该停就停别一味往前冲。

身强之命。丁火有整片木林在下面烧着你想不强都难。身强的人做事情有底气有冲劲但也容易太过主观觉得自己什么都能搞定。你需要在刚强中加一点柔软。听一听不同的声音尤其是那些跟你想法相反的人。

天乙贵人可能在地支中暗藏着。卯本身就是一个灵气很足的地支。你这副命格有灵气有冲劲有想法——三样都有但需要调和。

行业方向的话，喜金土泄木气。适合做跟精确性规范性相关的工作——金融法律项目管理。也适合做一些需要展现个人才华的领域。你的伤官加印星是聪明又有表达力的组合好好用。

大运如果走到金运（申酉）会是你比较顺的阶段——金能劈木让木材变成有用的器物。木太多反而会困住自己需要有人（或大运）来帮你剪一剪枝。"

你的命是一块璞玉。材料很好但需要雕琢。别急着证明自己先把基础打实。你还有很长时间可以用来发光。""",
}


def food_suggest(wx):
    """根据五行给饮食建议"""
    suggests = {
        "木": "多吃绿色蔬菜如菠菜、芹菜",
        "火": "多吃红色食物如红枣、枸杞",
        "土": "多吃黄色食物如小米、南瓜",
        "金": "多吃白色食物如白萝卜、雪梨",
        "水": "多吃黑色食物如黑豆、黑芝麻",
    }
    return suggests.get(wx, "均衡饮食")
