# -*- coding: utf-8 -*-
"""大六壬 — 完整排盘引擎 + 知识库查询"""

from datetime import date, datetime
from utils import load_json, TIANGAN, DIZHI

_LIUREN = None
_BAZI = None


def _load():
    global _LIUREN
    if _LIUREN is None:
        _LIUREN = load_json('liuren_ref.json')


# ============================================================
# 基础常量
# ============================================================
# 十二地支顺序（用作位置环）
ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 地盘：固定十二宫（以子为起始，逆时针分布在实际罗盘上，但运算时用线性顺序）
DIPAN = {zhi: i for i, zhi in enumerate(ZHI)}  # 子=0, 丑=1, ...

# 月将（根据节气）
# 中气 → 月将
YUEJIANG_ZHI = {
    "冬至": "丑", "大寒": "子", "雨水": "亥", "春分": "戌",
    "谷雨": "酉", "小满": "申", "夏至": "未", "大暑": "午",
    "处暑": "巳", "秋分": "辰", "霜降": "卯", "小雪": "寅",
}
# 或者按公历月份近似
YUEJIANG_MONTH = [None, "子", "亥", "戌", "酉", "申", "未", "午", "巳", "辰", "卯", "寅", "子"]
# 大寒~雨水=丑月，月将子；雨水~春分=寅月，月将亥；以此类推
# 简化：按中气日期
JIEQI_DETAIL = [
    # (名称, 月, 日, 月将)
    ("小寒", 1, 6, None),
    ("大寒", 1, 20, "子"),
    ("立春", 2, 4, None),
    ("雨水", 2, 19, "亥"),
    ("惊蛰", 3, 6, None),
    ("春分", 3, 21, "戌"),
    ("清明", 4, 5, None),
    ("谷雨", 4, 20, "酉"),
    ("立夏", 5, 6, None),
    ("小满", 5, 21, "申"),
    ("芒种", 6, 6, None),
    ("夏至", 6, 21, "未"),
    ("小暑", 7, 7, None),
    ("大暑", 7, 23, "午"),
    ("立秋", 8, 8, None),
    ("处暑", 8, 23, "巳"),
    ("白露", 9, 8, None),
    ("秋分", 9, 23, "辰"),
    ("寒露", 10, 8, None),
    ("霜降", 10, 24, "卯"),
    ("立冬", 11, 7, None),
    ("小雪", 11, 22, "寅"),
    ("大雪", 12, 7, None),
    ("冬至", 12, 22, "丑"),
]

# 日干寄宫
GAN_JIGONG = {
    "甲": "寅", "乙": "辰", "丙": "巳", "丁": "未",
    "戊": "巳", "己": "未", "庚": "申", "辛": "戌",
    "壬": "亥", "癸": "丑",
}

# 天将名称与地支对应（贵人居中）
TIANJIANG_NAMES = [
    ("贵人", "土", "吉"),
    ("螣蛇", "火", "凶"),
    ("朱雀", "火", "半凶"),
    ("六合", "木", "吉"),
    ("勾陈", "土", "凶"),
    ("青龙", "木", "吉"),
    ("天空", "土", "凶"),
    ("白虎", "金", "大凶"),
    ("太常", "土", "吉"),
    ("玄武", "水", "凶"),
    ("太阴", "金", "半吉"),
    ("天后", "水", "吉"),
]


# ============================================================
# 1. 确定月将
# ============================================================
def get_yuejiang(dt):
    """根据日期时间确定月将（即太阳所在之宫）"""
    for i in range(len(JIEQI_DETAIL) - 1, -1, -1):
        name, m, day, yj = JIEQI_DETAIL[i]
        jieqi_date = date(dt.year, m, day)
        if dt.date() >= jieqi_date and yj:
            return yj
    # 默认为冬至后 → 丑
    return "丑"


# ============================================================
# 2. 天盘：月将加时
# ============================================================
def calc_tianpan(yuejiang_zhi, shichen_zhi):
    """月将加时，顺布十二宫 → 天盘
    返回: dict {地盘地支: 天盘地支}
    """
    yj_idx = DIPAN[yuejiang_zhi]    # 月将在十二宫中的位置
    sc_idx = DIPAN[shichen_zhi]     # 时辰在地盘的位置

    # 月将加在时辰地支上
    # 天盘[sc_idx] = yj_idx  (时辰位安月将)
    # 然后顺布十二宫
    tianpan = {}
    for i in range(12):
        di_idx = i
        offset = (i - sc_idx) % 12
        tian_idx = (yj_idx + offset) % 12
        tianpan[ZHI[di_idx]] = ZHI[tian_idx]
    return tianpan


# ============================================================
# 3. 四课
# ============================================================
def calc_sike(day_gan, day_zhi, tianpan, yuejiang_zhi, shichen_zhi):
    """计算四课
    返回: list of 4 tuples [(天盘神, 地盘宫), ...]
    """
    # 第一课：日干寄宫的天盘上神
    gan_gong = GAN_JIGONG[day_gan]
    ke1_tian = tianpan[gan_gong]  # 寄宫地盘上的天盘神
    ke1_di = gan_gong

    # 第二课：第一课天盘神为地盘位置，再查其天盘上神
    ke2_tian = tianpan[ke1_tian]
    ke2_di = ke1_tian

    # 第三课：日支的天盘上神
    ke3_tian = tianpan[day_zhi]
    ke3_di = day_zhi

    # 第四课：第三课天盘神为地盘位置，再查其天盘上神
    ke4_tian = tianpan[ke3_tian]
    ke4_di = ke3_tian

    return [
        (ke1_tian, ke1_di),
        (ke2_tian, ke2_di),
        (ke3_tian, ke3_di),
        (ke4_tian, ke4_di),
    ]


# ============================================================
# 4. 三传（九宗法）
# ============================================================
def _wuxing_ke(t1, t2):
    """t1克t2? 返回True如果t1的五行克t2的五行"""
    wx_dizhi = {"子": "水", "丑": "土", "寅": "木", "卯": "木",
                "辰": "土", "巳": "火", "午": "火", "未": "土",
                "申": "金", "酉": "金", "戌": "土", "亥": "水"}
    ke_map = {"水": "火", "火": "金", "金": "木", "木": "土", "土": "水"}
    w1 = wx_dizhi.get(t1, "")
    w2 = wx_dizhi.get(t2, "")
    return ke_map.get(w1) == w2


def _is_yang_gan(gan):
    """判断日干阴阳"""
    yang_gan = {"甲", "丙", "戊", "庚", "壬"}
    return gan in yang_gan


def calc_sanchuan(day_gan, day_zhi, sike, tianpan):
    """九宗法求三传
    返回: (初传, 中传, 末传, 课体名称)
    """
    # 分析四课的克应
    # 第一课: 天盘sike[0][0] 地盘sike[0][1]
    #   - 天克地 = 上克下（from天克地）
    #   - 地克天 = 下克上（from地克天）

    # 四课的地盘和天盘
    ke_info = []
    for i, (tian, di) in enumerate(sike):
        info = {
            "id": i + 1,
            "tian": tian,
            "di": di,
            "xia_ke_shang": _wuxing_ke(di, tian),  # 下克上
            "shang_ke_xia": _wuxing_ke(tian, di),  # 上克下
        }
        ke_info.append(info)

    xia_ke_shang = [k for k in ke_info if k["xia_ke_shang"]]
    shang_ke_xia = [k for k in ke_info if k["shang_ke_xia"]]

    chu_chuan = None
    keti = ""

    # --- 1. 贼克 ---
    if xia_ke_shang:
        keti = "重审课" if len(xia_ke_shang) > 1 else "元首课(贼)"
        if len(xia_ke_shang) == 1:
            chu_chuan = xia_ke_shang[0]["tian"]
        else:
            # 比用
            chu_chuan = _biyong(xia_ke_shang, day_gan, tianpan)

    elif shang_ke_xia:
        keti = "知一课" if len(shang_ke_xia) > 1 else "元首课"
        if len(shang_ke_xia) == 1:
            chu_chuan = shang_ke_xia[0]["tian"]
        else:
            chu_chuan = _biyong(shang_ke_xia, day_gan, tianpan)

    # --- 2. 遥克 ---
    if chu_chuan is None:
        chu_chuan, keti = _yaoke(ke_info, day_gan, tianpan)

    # --- 3. 昴星 ---
    if chu_chuan is None:
        chu_chuan, keti = _maoxing(day_gan, tianpan)

    # 初传定了，中传来初传地盘上神，末传来中传地盘上神
    zhong_chuan = tianpan[chu_chuan]
    mo_chuan = tianpan[zhong_chuan]

    return chu_chuan, zhong_chuan, mo_chuan, keti


def _biyong(ke_list, day_gan, tianpan):
    """多个克，取与日干阴阳相比者"""
    yang_gan = _is_yang_gan(day_gan)
    yang_zhi = {"子", "寅", "辰", "午", "申", "戌"}

    same_yin_yang = []
    for k in ke_list:
        tian_yang = k["tian"] in yang_zhi
        if tian_yang == yang_gan:
            same_yin_yang.append(k)

    if len(same_yin_yang) == 1:
        return same_yin_yang[0]["tian"]
    elif len(same_yin_yang) > 1:
        # 涉害：取涉害深的（简化：取第一课优先）
        return same_yin_yang[0]["tian"]
    # fallback
    return ke_list[0]["tian"]


def _yaoke(ke_info, day_gan, tianpan):
    """遥克：四课无克，取遥克"""
    # 日干五行克某课天盘神 = 下克（我去克人）
    wx_tg = {"甲": "木", "乙": "木", "丙": "火", "丁": "火",
             "戊": "土", "己": "土", "庚": "金", "辛": "金",
             "壬": "水", "癸": "水"}
    wx_dz = {"子": "水", "丑": "土", "寅": "木", "卯": "木",
             "辰": "土", "巳": "火", "午": "火", "未": "土",
             "申": "金", "酉": "金", "戌": "土", "亥": "水"}
    ke_map = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

    dg_wx = wx_tg[day_gan]

    # 日干克神 → 取被克的神
    wo_ke_ren = []
    for k in ke_info:
        if ke_map.get(dg_wx) == wx_dz.get(k["tian"]):
            wo_ke_ren.append(k)

    if wo_ke_ren:
        if len(wo_ke_ren) == 1:
            return wo_ke_ren[0]["tian"], "遥克课(弹射)"
        else:
            return _biyong(wo_ke_ren, day_gan, tianpan), "遥克课(弹射)"

    # 神克日干 → 取克干的神
    ren_ke_wo = []
    for k in ke_info:
        if ke_map.get(wx_dz.get(k["tian"], "")) == dg_wx:
            ren_ke_wo.append(k)

    if ren_ke_wo:
        if len(ren_ke_wo) == 1:
            return ren_ke_wo[0]["tian"], "遥克课(蒿矢)"
        else:
            return _biyong(ren_ke_wo, day_gan, tianpan), "遥克课(蒿矢)"

    return None, ""


def _maoxing(day_gan, tianpan):
    """昴星：无克无遥"""
    yang = _is_yang_gan(day_gan)
    if yang:
        # 阳日：地盘酉上神
        return tianpan["酉"], "昴星课(虎视)"
    else:
        # 阴日：天盘酉下神
        for di, tian in tianpan.items():
            if tian == "酉":
                return di, "昴星课(冬蛇掩目)"
    # fallback
    return tianpan["酉"], "昴星课"


# ============================================================
# 5. 天将分配
# ============================================================
def _get_gui_ren_gong(day_gan, shichen_zhi):
    """根据日干和时辰确定贵人所在
    甲戊庚牛羊(昼丑夜未)，乙己鼠猴乡(昼子夜申)...
    """
    guiren_map = {
        "甲": ("丑", "未"), "戊": ("丑", "未"), "庚": ("丑", "未"),
        "乙": ("子", "申"), "己": ("子", "申"),
        "丙": ("亥", "酉"), "丁": ("亥", "酉"),
        "辛": ("午", "寅"),
        "壬": ("卯", "巳"), "癸": ("卯", "巳"),
    }
    day_ren, night_ren = guiren_map.get(day_gan, ("丑", "未"))

    # 简单的昼夜判断：卯辰巳午未申 = 昼，酉戌亥子丑寅 = 夜
    sc_idx = DIPAN[shichen_zhi]
    if 3 <= sc_idx <= 8:  # 卯~申
        return day_ren, "昼"
    else:
        return night_ren, "夜"


def _shun_ni_by_guiren(guiren_zhi):
    """贵人顺逆：亥子丑寅卯辰 = 顺，巳午未申酉戌 = 逆"""
    guiren_idx = DIPAN[guiren_zhi]
    if 0 <= guiren_idx <= 5:  # 亥子丑寅卯辰
        return "顺"
    else:  # 巳午未申酉戌
        return "逆"


def assign_tianjiang(tianpan, day_gan, shichen_zhi):
    """分配十二天将
    返回: dict {地盘位: (天将名, 五行, 吉凶)}
    """
    guiren_zhi, day_night = _get_gui_ren_gong(day_gan, shichen_zhi)
    direction = _shun_ni_by_guiren(guiren_zhi)

    # 天将列表（从贵人开始）
    # 顺序：贵人 螣蛇 朱雀 六合 勾陈 青龙 天空 白虎 太常 玄武 太阴 天后

    # 找到贵人在天盘的位置
    guiren_tianpan_pos = guiren_zhi  # 贵人在天盘所临之地盘位

    # 天将按顺序排布
    result = {}
    guiren_idx = DIPAN[guiren_zhi]
    step = 1 if direction == "顺" else -1

    for i in range(12):
        pos_idx = (guiren_idx + i * step) % 12
        result[ZHI[pos_idx]] = TIANJIANG_NAMES[i]

    return result, guiren_zhi, day_night, direction


# ============================================================
# 6. 遁干
# ============================================================
def calc_dungan(shichen_zhi, yuejiang_zhi, tianpan):
    """五鼠遁时，给天盘十二宫配天干
    返回: dict {地盘位: 天干}
    """
    # 时干：按五鼠遁
    wushu = {
        "甲": "甲", "己": "甲",
        "乙": "丙", "庚": "丙",
        "丙": "戊", "辛": "戊",
        "丁": "庚", "壬": "庚",
        "戊": "壬", "癸": "壬",
    }

    shichen_idx = DIPAN[shichen_zhi]

    # 需要日干来确定时干起法...实际上遁干独立于日干
    # 简化：以时辰地支的遁干为基础，十二宫依序排列
    # 标准的五鼠遁需要日干，但我们此时可能没有
    # 简化为以甲子起
    dungan = {}
    for i, zhi in enumerate(ZHI):
        dungan[zhi] = TIANGAN[i % 10]
    return dungan


# ============================================================
# 7. 神煞
# ============================================================
def calc_liuren_shensha(day_gan, day_zhi, year_zhi, month_zhi):
    """计算六壬相关神煞"""
    shensha = {}

    # 天乙贵人
    guiren_map = {
        "甲": ["丑", "未"], "戊": ["丑", "未"], "庚": ["丑", "未"],
        "乙": ["子", "申"], "己": ["子", "申"],
        "丙": ["亥", "酉"], "丁": ["亥", "酉"],
        "辛": ["午", "寅"],
        "壬": ["卯", "巳"], "癸": ["卯", "巳"],
    }
    shensha["天乙贵人"] = guiren_map.get(day_gan, ["丑", "未"])

    # 文昌
    wenchang = {"甲": "巳", "乙": "午", "丙": "申", "丁": "酉", "戊": "申",
                "己": "酉", "庚": "亥", "辛": "子", "壬": "寅", "癸": "卯"}
    shensha["文昌"] = wenchang.get(day_gan, "")

    # 驿马
    yima_map = {"寅午戌": "申", "申子辰": "寅", "巳酉丑": "亥", "亥卯未": "巳"}
    for combo, ma in yima_map.items():
        if year_zhi in combo:
            shensha["驿马"] = ma
            break

    # 桃花
    taohua_map = {"寅午戌": "卯", "申子辰": "酉", "巳酉丑": "午", "亥卯未": "子"}
    for combo, hua in taohua_map.items():
        if year_zhi in combo:
            shensha["桃花"] = hua
            break

    # 羊刃
    yangren = {"甲": "卯", "乙": "寅", "丙": "午", "丁": "巳", "戊": "午",
               "己": "巳", "庚": "酉", "辛": "申", "壬": "子", "癸": "亥"}
    shensha["羊刃"] = yangren.get(day_gan, "")

    # 空亡
    xun_kong = {
        ("甲", "子"): ("戌", "亥"), ("甲", "戌"): ("申", "酉"),
        ("甲", "申"): ("午", "未"), ("甲", "午"): ("辰", "巳"),
        ("甲", "辰"): ("寅", "卯"), ("甲", "寅"): ("子", "丑"),
    }
    xun_tou_gan = TIANGAN[(TIANGAN.index(day_gan) // 5) * 5]
    xun_tou_zhi = ZHI[(ZHI.index(day_zhi) // 6) * 6]
    for (tg, tz), kong in xun_kong.items():
        if tg == xun_tou_gan and tz == xun_tou_zhi:
            shensha["空亡"] = list(kong)
            break

    # 德神
    de_map = {"甲": "寅", "乙": "申", "丙": "巳", "丁": "午", "戊": "巳",
              "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子"}
    shensha["德神"] = de_map.get(day_gan, "")

    return shensha


# ============================================================
# 8. 完整排盘
# ============================================================
def full_pan(birth_date=None, birth_hour=12):
    """大六壬完整排盘
    birth_date: date 对象（默认今天）
    birth_hour: int 0-23（默认12时）
    返回完整的天地盘、四课、三传信息
    """
    if birth_date is None:
        birth_date = date.today()

    dt = datetime.combine(birth_date, datetime.min.time().replace(hour=birth_hour))

    # 时辰地支
    hour_zhi_idx = (birth_hour + 1) // 2 % 12
    shichen_zhi = ZHI[hour_zhi_idx]

    # 日干支（用八字引擎的日柱算法）
    from bazi import calc_day_pillar
    day_gz = calc_day_pillar(birth_date)
    day_gan = day_gz[0][0]
    day_zhi = day_gz[0][1]

    # 年干支（简化）
    from bazi import calc_year_pillar
    year_gz_idx = calc_year_pillar(birth_date)
    year_gan = TIANGAN[year_gz_idx % 10]
    year_zhi = ZHI[year_gz_idx % 12]

    # 月将
    yuejiang_zhi = get_yuejiang(dt)

    # 天盘
    tianpan = calc_tianpan(yuejiang_zhi, shichen_zhi)

    # 四课
    sike = calc_sike(day_gan, day_zhi, tianpan, yuejiang_zhi, shichen_zhi)

    # 三传
    chu_chuan, zhong_chuan, mo_chuan, keti = calc_sanchuan(day_gan, day_zhi, sike, tianpan)

    # 天将
    tianjiang, guiren_zhi, day_night, direction = assign_tianjiang(tianpan, day_gan, shichen_zhi)

    # 遁干
    dungan = calc_dungan(shichen_zhi, yuejiang_zhi, tianpan)

    # 神煞
    shensha = calc_liuren_shensha(day_gan, day_zhi, year_zhi, ZHI[(dt.month - 1) % 12])

    # 四课格式化
    sike_formatted = []
    for i, (tian, di) in enumerate(sike):
        wx_t = _zhi_wuxing(tian)
        wx_d = _zhi_wuxing(di)
        ke_rel = ""
        if _wuxing_ke(di, tian):
            ke_rel = "下克上"
        elif _wuxing_ke(tian, di):
            ke_rel = "上克下"
        sike_formatted.append({
            "name": f"第{i+1}课",
            "tianpan": tian,
            "dipan": di,
            "tian_wx": wx_t,
            "di_wx": wx_d,
            "ke": ke_rel,
        })

    # 白话解读
    pan_result = {
        "date": birth_date.isoformat(),
        "hour": birth_hour,
        "shichen": shichen_zhi,
        "day_ganzhi": day_gz[0],
        "day_gan": day_gan,
        "day_zhi": day_zhi,
        "year_zhi": year_zhi,
        "yuejiang": yuejiang_zhi,
        "yuejiang_name": _yuejiang_name(yuejiang_zhi),
        "tianpan": tianpan,
        "sike": sike_formatted,
        "sanchuan": {
            "chu_chuan": chu_chuan,
            "zhong_chuan": zhong_chuan,
            "mo_chuan": mo_chuan,
            "keti": keti,
            "formula": f"{keti}：初传{chu_chuan}，中传{zhong_chuan}，末传{mo_chuan}",
        },
        "tianjiang": tianjiang,
        "guiren": guiren_zhi,
        "day_night": day_night,
        "direction": direction,
        "dungan": dungan,
        "shensha": shensha,
    }
    pan_result["interpretation"] = generate_interpretation(pan_result)

    # AI 深度解读（可插拔）
    try:
        from ai_interpreter import get_interpreter
        ai = get_interpreter()
        if ai.enabled:
            ai_data = {
                "date": pan_result["date"],
                "day_ganzhi": pan_result["day_ganzhi"],
                "day_gan": pan_result["day_gan"],
                "shichen": pan_result["shichen"],
                "yuejiang": pan_result["yuejiang"],
                "yuejiang_name": pan_result["yuejiang_name"],
                "tianpan": pan_result["tianpan"],
                "sike": pan_result["sike"],
                "sanchuan": pan_result["sanchuan"],
                "tianjiang": pan_result["tianjiang"],
                "shensha": pan_result["shensha"],
            }
            ai_text = ai.interpret("liuren", ai_data)
            if ai_text:
                pan_result["interpretation"] += f"\n\n【凤年真人深度详解】\n{ai_text}"
    except Exception:
        pass

    return pan_result


def _zhi_wuxing(zhi):
    m = {"子": "水", "丑": "土", "寅": "木", "卯": "木",
         "辰": "土", "巳": "火", "午": "火", "未": "土",
         "申": "金", "酉": "金", "戌": "土", "亥": "水"}
    return m.get(zhi, "?")


def _yuejiang_name(zhi):
    names = {"亥": "登明", "戌": "河魁", "酉": "从魁", "申": "传送",
             "未": "小吉", "午": "胜光", "巳": "太乙", "辰": "天罡",
             "卯": "太冲", "寅": "功曹", "丑": "大吉", "子": "神后"}
    return names.get(zhi, zhi)


# ============================================================
# 9. 白话解读（200字+）
# ============================================================
def generate_interpretation(pan):
    """根据排盘结果生成详细的白话解读"""
    sc = pan["sanchuan"]
    keti = sc["keti"]
    chu = sc["chu_chuan"]
    zhong = sc["zhong_chuan"]
    mo = sc["mo_chuan"]

    # 课体解读
    keti_analysis = {
        "元首课": "一上克下，为元首课。主臣忠子孝，君令臣行之象。宜顺势而为，不可越级妄动。问事主先难后易，上级或有指令下达。",
        "元首课(贼)": "一下克上，为元首课之贼格。主下谋上、内忧外患。凡事需防内部变故或下属反叛。",
        "重审课": "多下克上，为重审课。主事宜再三审视，不可轻易决定。暗中有阻力，需反复权衡。",
        "知一课": "多上克下，为知一课。主面临多重选择，需知一而止，不可贪多。取舍之间，见智慧。",
        "遥克课(弹射)": "日干克神，为弹射格。主我主动出击，事在人为。但需防用力过猛，反伤自身。",
        "遥克课(蒿矢)": "神克日干，为蒿矢格。主外事来扰，如暗箭难防。宜静观其变，以逸待劳。",
        "昴星课(虎视)": "昴星虎视，阳日取酉上神。主事多虚浮，如虎视眈眈而未必真动。宜以静制动。",
        "昴星课(冬蛇掩目)": "昴星冬蛇掩目，阴日取酉下神。主暗昧不明，事多隐伏。宜明察秋毫，防患未然。",
    }

    keti_desc = keti_analysis.get(keti, f"此课为{keti}，需结合天地盘与三传综合判断。")

    # 三传分析
    chu_wx = _zhi_wuxing(chu)
    zhong_wx = _zhi_wuxing(zhong)
    mo_wx = _zhi_wuxing(mo)

    # 三传生克关系
    chu_zhong_rel = _describe_ke_relation(chu, zhong, "初传", "中传")
    zhong_mo_rel = _describe_ke_relation(zhong, mo, "中传", "末传")

    # 天将看吉凶
    tianjiang = pan["tianjiang"]
    jiang_ji = []
    jiang_xiong = []
    for zhi, (name, wx, jx) in tianjiang.items():
        if jx in ("吉", "大吉"):
            jiang_ji.append(f"{zhi}宫{name}")
        elif jx in ("凶", "大凶"):
            jiang_xiong.append(f"{zhi}宫{name}")

    # 综合判断
    if jiang_ji and not jiang_xiong:
        overall = "天将多在吉方，整体运势向好。贵人得力，青龙在位，宜积极进取。"
    elif jiang_xiong and not jiang_ji:
        overall = "天将多在凶方，运势有阻。白虎玄武当道，宜谨慎行事，退守待时。凡事三思，不可冒进。"
    else:
        overall = "天将吉凶参半，运势起伏不定。关键看三传走势：若初传吉则事发良好，末传吉则结局圆满。"

    # 拼接完整解读
    analysis = f"""【课体总论】
{keti_desc}

【三传走势】
初传{chu}（属{chu_wx}）发用，为事发之始。中传{zhong}（属{zhong_wx}），为事之中途，{chu_zhong_rel}。末传{mo}（属{mo_wx}），为事之结局，{zhong_mo_rel}。
{_sanchuan_story(chu, zhong, mo, chu_wx, zhong_wx, mo_wx)}

【天将分布】
吉将所在：{'、'.join(jiang_ji) if jiang_ji else '无'}。
凶将所在：{'、'.join(jiang_xiong) if jiang_xiong else '无'}。
贵人{pan['guiren']}，{pan['day_night']}{pan['direction']}而行。{_guiren_advice(pan['guiren'], pan['day_night'])}

【神煞提示】
{_shensha_advice(pan['shensha'])}

【综合论断】
{overall}

六壬课式虽繁，然核心在一气之流行。初传为因，中传为过程，末传为果。道友观此三传，即可知事态之大势。然天机虽现，人事在己。顺应时势者昌，逆势而行者亡。福生无量天尊！"""

    return analysis


def _describe_ke_relation(z1, z2, n1, n2):
    """描述两个地支间的生克关系"""
    if _wuxing_ke(z1, z2):
        return f"{n1}克{n2}，前段压制后段，事有阻碍，需克服困难方能推进"
    elif _wuxing_ke(z2, z1):
        return f"{n2}克{n1}，后段反制前段，先松后紧，后期压力渐增"
    elif _zhi_wuxing(z1) == _zhi_wuxing(z2):
        return f"五行相同，气场平稳过渡，事态连贯，无大起落"
    return f"五行不克，气场顺畅传递，前后呼应"


def _sanchuan_story(chu, zhong, mo, cw, zw, mw):
    """三传故事化解读"""
    stories = []
    if cw == "木":
        stories.append("事之初如木之生长，生机勃发，有新机萌动")
    elif cw == "火":
        stories.append("事之初如火之燎原，来势迅猛，需雷霆手段")
    elif cw == "土":
        stories.append("事之初如土之厚重，起步稳健，但进展较缓")
    elif cw == "金":
        stories.append("事之初如金之锋锐，果断出击，但刚极易折")
    elif cw == "水":
        stories.append("事之初如水之流动，灵活多变，但方向未定")

    if mw == "木":
        stories.append("结局如春木繁荣，有生长收获之喜")
    elif mw == "火":
        stories.append("结局如夏日烈炎，声势浩大，但需防物极必反")
    elif mw == "土":
        stories.append("结局如厚土载物，稳定踏实，虽不惊艳但根基牢固")
    elif mw == "金":
        stories.append("结局如秋金肃杀，有决断分离之象，宜当机立断")
    elif mw == "水":
        stories.append("结局如冬水归藏，事态趋于平静，宜顺势退守")

    return "。".join(stories) + "。"


def _guiren_advice(guiren_zhi, day_night):
    """贵人方位建议"""
    dir_map = {"子": "正北", "丑": "东北偏北", "寅": "东北偏东", "卯": "正东",
               "辰": "东南偏东", "巳": "东南偏南", "午": "正南", "未": "西南偏南",
               "申": "西南偏西", "酉": "正西", "戌": "西北偏西", "亥": "西北偏北"}
    d = dir_map.get(guiren_zhi, guiren_zhi)
    if day_night == "昼":
        return f"贵人临{d}方，昼贵得力，白日行事较为顺遂，宜在白天处理重要事务。"
    return f"贵人临{d}方，夜贵当值，夜间或有暗助，晚间静候佳音亦可。"


def _shensha_advice(shensha):
    """神煞建议"""
    tips = []
    if "天乙贵人" in shensha:
        tips.append("天乙贵人照命，逢凶化吉，多得贵人提携")
    if "驿马" in shensha:
        tips.append(f"驿马在{shensha['驿马']}，主动象，宜出行、调动、变化")
    if "桃花" in shensha:
        tips.append("桃花入课，人际关系活跃，但需防感情用事")
    if "空亡" in shensha:
        kong = "、".join(shensha["空亡"]) if isinstance(shensha["空亡"], list) else shensha["空亡"]
        tips.append(f"空亡在{kong}，部分计划恐落空，宜脚踏实地")
    if "羊刃" in shensha:
        tips.append(f"羊刃在{shensha['羊刃']}，刚烈伤身，凡事不可冲动")
    return "；".join(tips) if tips else "本课未见特殊神煞，运势平稳。"


# ============================================================
# 知识库查询（保留原有功能）
# ============================================================
def get_overview():
    _load()
    return _LIUREN.get("overview", "")


def get_12_generals():
    _load()
    return _LIUREN.get("十二天将", {})


def get_general(name):
    _load()
    return _LIUREN.get("十二天将", {}).get(name)


def get_shensha():
    _load()
    return _LIUREN.get("神煞", {})


def get_kejing():
    _load()
    return _LIUREN.get("课经", {})


def get_kejing_detail(name):
    _load()
    return _LIUREN.get("课经", {}).get(name)


def get_bifa():
    _load()
    return _LIUREN.get("毕法赋", [])


def get_dizhi_xiangyi(zhi):
    _load()
    return _LIUREN.get("十二地支象意", {}).get(zhi)


def search(query):
    _load()
    results = []

    def _search_dict(d, path=""):
        for k, v in d.items():
            current_path = f"{path}/{k}" if path else k
            if query in str(k):
                results.append({"path": current_path, "content": str(v)[:200]})
            if isinstance(v, dict):
                _search_dict(v, current_path)
            elif isinstance(v, str) and query in v:
                results.append({"path": current_path, "content": v[:200]})
            elif isinstance(v, list):
                for item in v:
                    if query in str(item):
                        results.append({"path": current_path, "content": str(item)[:200]})

    _search_dict(_LIUREN)
    return results
