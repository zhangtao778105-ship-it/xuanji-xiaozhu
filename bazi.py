# -*- coding: utf-8 -*-
"""八字命盘引擎 — 四柱推算、十神、五行、纳音、大运、神煞"""

from datetime import date
from utils import (
    load_json, solar_to_lunar, TIANGAN, DIZHI,
    JIEQI_APPROX,
)

_BAZI = None


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

    # 详细分析（静态模板）
    analysis = generate_analysis(pillars, wx_counts, yongshen, shensha, dayun, gender, shengxiao, day_gan, day_zhi)

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
def generate_analysis(pillars, wx_counts, yongshen, shensha, dayun, gender, shengxiao, day_gan, day_zhi):
    """生成详细的命盘白话分析（至少200字）"""
    _load()
    wuxing_map = _BAZI["wuxing_map"]
    dwx = yongshen["day_master_wuxing"]

    # 五行性格特征
    wx_char = {
        "木": "仁慈善良，有恻隐之心，志向高远，如大树般正直向上。但有时过于耿直，不擅变通。",
        "火": "热情奔放，积极向上，有领导才能和感染力。但有时急躁冲动，缺乏耐心。",
        "土": "诚信敦厚，稳重踏实，包容万物。但有时过于保守，缺乏灵活性。",
        "金": "刚毅果断，讲义气，是非分明。但有时过于刚硬，容易得罪人。",
        "水": "聪明灵活，善于变通，足智多谋。但有时心思太活，容易三心二意。",
    }
    char_desc = wx_char.get(dwx, "性格平和。")

    # 五行平衡分析
    wx_list = [(k, v) for k, v in wx_counts.items()]
    wx_list.sort(key=lambda x: -x[1])
    most_wx = wx_list[0]
    least_wx = wx_list[-1]

    # 十神分析
    shishen_list = [p["shishen"] for p in pillars if p["shishen"] != "日主"]
    shishen_str = "、".join(shishen_list)

    # 格局简评
    body = yongshen["body_type"]
    ys = "、".join(yongshen["yongshen"])
    body_comment = ""
    if body == "身强":
        body_comment = f"日主{dwx}身强，如大树参天，根深叶茂。命主个性刚毅，有主见，能独当一面，行事果断。但也容易过于自我，宜多听取他人意见。命局喜{ys}来平衡，逢{ys}之岁运最为得利。"
    else:
        body_comment = f"日主{dwx}身弱，如嫩苗初生，需细心呵护。命主性情温和，善于合作，人缘不错。但遇事容易犹豫不决，需借助外力方能成事。命局喜{ys}来扶助，逢{ys}之岁运较为有利。"

    # 性格详述
    personality = ""
    if "正官" in shishen_str:
        personality += "命带正官，为人正直有责任感，遵纪守法，适合公职或在规范化的环境中发展。"
    if "七杀" in shishen_str:
        personality += "命带七杀，有魄力有担当，不畏艰难。但也容易冲动，需注意控制情绪。"
    if "正印" in shishen_str:
        personality += "命带正印，聪慧好学，悟性较高，多得长辈贵人扶持。"
    if "偏印" in shishen_str:
        personality += "命带偏印，思维独特，有艺术天赋或特殊技能。但有时想法偏执。"
    if "正财" in shishen_str:
        personality += "命带正财，重视物质生活，勤俭持家，财运稳健但来得慢。"
    if "偏财" in shishen_str:
        personality += "命带偏财，有投资眼光，善于把握商机，但财运起伏较大。"
    if "食神" in shishen_str:
        personality += "命带食神，天性乐观温和，有口福也有创造力，懂得享受生活。"
    if "伤官" in shishen_str:
        personality += "命带伤官，才华横溢，聪明外露。但锋芒过盛，需防口舌是非。"
    if "比肩" in shishen_str:
        personality += "命带比肩，自尊心强，兄弟缘深。但也容易与人竞争或攀比。"
    if "劫财" in shishen_str:
        personality += "命带劫财，社交能力强，朋友众多。但需防因朋友而破财。"

    # 神煞补充
    shensha_comment = ""
    for name, val in shensha.items():
        if name == "天乙贵人":
            shensha_comment += f"命带天乙贵人，一生多得贵人相助，逢凶化吉。"
        elif name == "文昌":
            shensha_comment += f"命带文昌星，学业运佳，适合读书深造，文笔口才俱佳。"
        elif name == "驿马":
            shensha_comment += f"命带驿马，一生多动少静，宜从事外勤、贸易、交通等行业，不宜久居一隅。"
        elif name == "桃花":
            shensha_comment += f"命带桃花，人缘异性缘佳，容貌气质较出众。但需注意感情纠葛。"
        elif name == "羊刃":
            shensha_comment += f"命带羊刃，个性刚烈急躁，做事有魄力但容易冲动行事，宜修身养性。"
        elif name == "空亡":
            shensha_comment += f"命逢空亡，部分运势虚而不实，宜脚踏实地，不宜做空中楼阁之梦。"

    if not shensha_comment:
        shensha_comment = "命盘未见特殊神煞，运势较为平稳。"

    # 大运提示
    dayun_tip = ""
    if dayun["dayun"]:
        first_dayun = dayun["dayun"][0]
        dayun_tip = f"起运{dayun['qiyun_age']}岁，为{dayun['direction']}。首步大运{first_dayun['ganzhi']}({first_dayun['nayin']})，行{first_dayun['age']}岁。大运为人生之各个阶段，每十年一换，逢交运之年宜多加注意。"

    # 健康建议
    wx_body = {"木": "肝胆", "火": "心血管", "土": "脾胃", "金": "肺与呼吸道", "水": "肾脏与泌尿系统"}
    health_wx = wx_body.get(least_wx[0], "整体")
    health = f"五行{least_wx[0]}偏弱，需留意{health_wx}方面的健康。平时宜多补充{least_wx[0]}属性的食物和活动，如{food_suggest(least_wx[0])}。"

    # 行业建议
    industry = f"宜从事与{'、'.join(yongshen['yongshen'])}相关的行业。"

    analysis = f"""【命理综述】
命主为{gender}命，生于{'-'.join([p['ganzhi'] for p in pillars])}八字，属{shengxiao}。天干透出{shishen_str}，地支藏干丰富。

【性格特征】
日主{dwx}，五行中{most_wx[0]}最旺（{most_wx[1]}个）、{least_wx[0]}最弱（{least_wx[1]}个）。{char_desc}{personality}

【格局分析】
{body_comment}

【神煞】
{shensha_comment}

【大运起止】
{dayun_tip}

【健康养生】
{health}

【行业方向】
{industry}

【总论】
命主的命格以{dwx}为日主，{'身强' if body == '身强' else '身弱'}之命。一生运势随大运流转而变化。{'中年之后运势渐旺，' if body == '身强' else '早年得扶助则顺遂，'}宜借助{'、'.join(yongshen['yongshen'])}之五行力量。命途虽有起落，但只要顺应时势，积极进取，必能有所作为。道法自然，知命而不认命，方为真智慧。"""

    return analysis


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
