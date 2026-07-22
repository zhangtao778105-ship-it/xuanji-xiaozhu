# -*- coding: utf-8 -*-
"""每日运势引擎 — 基于日期计算当日卦象和运势（含宜/忌/幸运颜色/方位指引）

运势文案生成逻辑：
1. 日期哈希确定当日卦象（64卦均匀分布）
2. 日期哈希确定变体索引（同一天同一卦结果相同）
3. 从 hexagrams.json 中取该卦的真实经义（卦辞/彖辞/大象辞/注释）构造运势文案
4. 从 daily_fortunes.json 中取宜/忌/幸运颜色（结构化数据）
5. 从上卦/下卦推导当日吉方与坐向建议
"""

import hashlib
import re
from datetime import date, datetime
from zoneinfo import ZoneInfo
from utils import load_json, TIANGAN, DIZHI
from config import TIMEZONE

# 八卦方位五行映射
_TRIGRAM_DIR = {
    "乾": {"direction": "西北", "wuxing": "金", "nature": "天", "symbol": "☰"},
    "坤": {"direction": "西南", "wuxing": "土", "nature": "地", "symbol": "☷"},
    "震": {"direction": "东",   "wuxing": "木", "nature": "雷", "symbol": "☳"},
    "巽": {"direction": "东南", "wuxing": "木", "nature": "风", "symbol": "☴"},
    "坎": {"direction": "北",   "wuxing": "水", "nature": "水", "symbol": "☵"},
    "離": {"direction": "南",   "wuxing": "火", "nature": "火", "symbol": "☲"},
    "艮": {"direction": "东北", "wuxing": "土", "nature": "山", "symbol": "☶"},
    "兌": {"direction": "西",   "wuxing": "金", "nature": "泽", "symbol": "☱"},
}

_HEXAGRAMS = None
_DAILY_FORTUNES = None
_HEX_BY_ID = None
_HEX_BY_NAME = None


def _today():
    """返回时区感知的今日日期（解决 PythonAnywhere UTC 时区问题）"""
    try:
        tz = ZoneInfo(TIMEZONE)
    except Exception:
        tz = ZoneInfo("Asia/Shanghai")
    return datetime.now(tz).date()


def _load():
    """懒加载数据文件，建立索引"""
    global _HEXAGRAMS, _DAILY_FORTUNES, _HEX_BY_ID, _HEX_BY_NAME
    if _HEXAGRAMS is None:
        _HEXAGRAMS = load_json('hexagrams.json')
        _HEX_BY_ID = {}
        _HEX_BY_NAME = {}
        for key, hd in _HEXAGRAMS.items():
            _HEX_BY_ID[hd["id"]] = (key, hd)
            _HEX_BY_NAME[hd["name_cn"]] = (key, hd)
    if _DAILY_FORTUNES is None:
        try:
            _DAILY_FORTUNES = load_json('daily_fortunes.json')
        except Exception:
            _DAILY_FORTUNES = []


def daily_hexagram(d=None):
    """根据日期计算当日卦象（MD5(date) % 64 + 1，均匀分布）"""
    if d is None:
        d = _today()
    day_str = d.isoformat()
    hash_val = int(hashlib.md5(day_str.encode()).hexdigest(), 16)
    idx = (hash_val % 64) + 1

    _load()
    if idx in _HEX_BY_ID:
        key, hex_data = _HEX_BY_ID[idx]
        return hex_data, key
    return None, None


def daily_ganzhi(d=None):
    """计算当日干支（简化版：以1900-01-01甲戌日为基准）"""
    if d is None:
        d = _today()
    base = date(1900, 1, 1)
    base_gz = 10  # 1900-01-01是甲戌日（甲戌在60甲子中排第11，0-based=10）
    days_diff = (d - base).days
    gz_idx = (base_gz + days_diff) % 60
    gan = TIANGAN[gz_idx % 10]
    zhi = DIZHI[gz_idx % 12]
    return gan + zhi, gz_idx


def _birthday_fortune(d):
    """生日彩蛋：7月12日——乾卦上吉，专属运势"""
    _load()
    gz_str, gz_idx = daily_ganzhi(d)

    # 取乾卦数据（卦序第1）
    hex_key = "111111"
    hex_data = _HEXAGRAMS.get(hex_key)
    if not hex_data:
        # 极端降级：拿任意卦
        hex_data, hex_key = list(_HEXAGRAMS.items())[0]

    return {
        "date": d.isoformat(),
        "day_ganzhi": gz_str,
        "hexagram": hex_data,
        "hexagram_key": hex_key,
        "level": "上吉",
        "fortune": (
            "今日乾卦当值，天行健，君子以自强不息。"
            "此日生于天地交泰之时，得乾元之气，命中带贵。"
            "一生有贵人相助，遇难呈祥，逢凶化吉。"
            "胸怀大志者终有所成，心存善念者福泽绵长。"
            "今日宜开怀畅饮，与所爱之人共度良辰。"
            "生日快乐——凤年真人稽首。"
        ),
        "yi": "宜：庆祝生辰开怀畅饮展望未来许下心愿陪伴家人朋友欢聚享用美味",
        "ji": "忌：妄自菲薄忧愁焦虑辜负良辰美景",
        "lucky_colors": ["金色", "红色", "紫色"],
        "direction": _direction_guidance(hex_data, 0),
        "da_xiang": hex_data.get("da_xiang_ci", ""),
        "gua_ci": hex_data.get("gua_ci", ""),
        "variant_idx": 0,
    }


def daily_fortune(d=None):
    """生成每日综合运势（含宜/忌/幸运颜色）

    流程：
    1. 日期 → MD5 → 卦象ID（确定性，每天一卦）
    2. 卦象数据 + 日期哈希变体 → 运势文案（从卦象经义中提取）
    3. 从 daily_fortunes.json 取宜/忌/颜色（按卦名+变体匹配）
    """
    if d is None:
        d = _today()

    # 生日彩蛋：每年7月12日必定上吉
    if d.month == 7 and d.day == 12:
        return _birthday_fortune(d)

    hex_data, key = daily_hexagram(d)
    gz_str, gz_idx = daily_ganzhi(d)

    if not hex_data:
        return {"error": "无法获取今日卦象"}

    gua_name = hex_data["name_cn"]
    da_xiang = hex_data.get("da_xiang_ci", "")
    gua_ci = hex_data.get("gua_ci", "")

    # 日期哈希 → 变体索引（0~4）
    day_hash = int(hashlib.md5(d.isoformat().encode()).hexdigest(), 16)
    variant_idx = day_hash % 5

    # 从卦象经义生成运势文案
    fortune_text = _build_fortune_text(hex_data, variant_idx)

    # 从 daily_fortunes.json 取宜/忌/颜色
    yi, ji, lucky_colors = _get_yi_ji_colors(gua_name, hex_data, variant_idx)

    # 卦象吉凶判断
    level = _judge_level(gua_name)

    # 方位指引
    direction = _direction_guidance(hex_data, variant_idx)

    return {
        "date": d.isoformat(),
        "day_ganzhi": gz_str,
        "hexagram": hex_data,
        "hexagram_key": key,
        "level": level,
        "fortune": fortune_text,
        "yi": yi,
        "ji": ji,
        "lucky_colors": lucky_colors,
        "direction": direction,
        "da_xiang": da_xiang,
        "gua_ci": gua_ci,
        "variant_idx": variant_idx,
    }


def _direction_guidance(hex_data, variant_idx):
    """从卦象的上卦/下卦推导当日吉方与坐向建议

    上卦为天时之气（外），下卦为地势之基（内）。
    吉方取上卦方位为主，下卦方位为辅。
    坐向建议：面朝吉方而坐，吸纳该卦五行之气。
    """
    upper = hex_data.get("upper_trigram", "")
    lower = hex_data.get("lower_trigram", "")
    up_info = _TRIGRAM_DIR.get(upper, {})
    lo_info = _TRIGRAM_DIR.get(lower, {})

    if not up_info or not lo_info:
        return None

    up_dir = up_info["direction"]
    lo_dir = lo_info["direction"]
    up_elem = up_info["wuxing"]

    # 五行对应的方位寄语
    elem_phrases = {
        "金": "金气主决断，利决策、签约、谈判",
        "木": "木气主生发，利学习、创作、新计划",
        "水": "水气主智慧，利思考、规划、沟通交流",
        "火": "火气主热情，利社交、表达、展现自我",
        "土": "土气主稳重，利理财、置业、夯实基础",
    }

    # 坐向建议（5种变体增加变化）
    seat_templates = [
        f"面朝{up_dir}而坐，背靠{lo_dir}为佳",
        f"办公桌宜朝向{up_dir}方",
        f"今日重要场合面{up_dir}方最为有利",
        f"座位靠{lo_dir}墙，面{up_dir}方，稳中求进",
        f"向{up_dir}方吸纳{up_elem}气，事半功倍",
    ]
    seat = seat_templates[variant_idx % len(seat_templates)]

    # 组装方位说明
    if upper == lower:
        # 上下卦相同（八纯卦），方位唯一
        reason = (
            f"今日「{upper}」卦纯{'气' if variant_idx % 2 == 0 else '象'}当值，"
            f"{up_dir}方为{up_info['nature']}之位，{elem_phrases.get(up_elem, '气场最旺')}"
        )
        direction_text = f"{up_dir}方"
        return {
            "primary": up_dir,
            "secondary": None,
            "display": direction_text,
            "seat": seat,
            "reason": reason,
            "wuxing": up_elem,
            "nature": up_info["nature"],
            "up_trigram": upper,
            "lo_trigram": lower,
        }

    # 上下卦不同
    reason_templates = [
        f"上卦{up_info['symbol']}{upper}为{up_info['nature']}，居{up_dir}方，主外缘机遇；"
        f"下卦{lo_info['symbol']}{lower}为{lo_info['nature']}，居{lo_dir}方，主内在根基",
        f"天时在{up_dir}（{upper}），地势在{lo_dir}（{lower}），"
        f"{elem_phrases.get(up_elem, '宜顺势而动')}",
        f"{upper}上{lower}下，{up_dir}方得天时之气，"
        f"今日关键事务优先面朝此方",
        f"{up_info['nature']}行{up_dir}，{lo_info['nature']}守{lo_dir}，"
        f"一动一静，阴阳相济",
        f"卦象{up_info['symbol']}上{lo_info['symbol']}下，"
        f"主{up_dir}方{up_elem}气流动，宜顺势而为",
    ]
    reason = reason_templates[variant_idx % len(reason_templates)]

    direction_text = f"{up_dir}方为主，{lo_dir}方为辅"
    return {
        "primary": up_dir,
        "secondary": lo_dir,
        "display": direction_text,
        "seat": seat,
        "reason": reason,
        "wuxing": up_elem,
        "nature": up_info["nature"],
        "up_trigram": upper,
        "lo_trigram": lower,
    }


def _build_fortune_text(hex_data, variant_idx):
    """从卦象经义数据生成运势文案

    文案 = 大象旨要 + 角度解读 + 收尾句
    5种变体对应5种解读角度：事业/人际/财运/健康/综合
    """
    gua_name = hex_data["name_cn"]
    gua_ci = hex_data.get("gua_ci", "")
    da_xiang_ci = hex_data.get("da_xiang_ci", "")
    commentaries = hex_data.get("commentaries", [])

    # 从大象辞中提取核心指引
    xiang_core = _extract_xiang_core(da_xiang_ci)

    # 根据变体选择角度
    angles = ["career", "love", "wealth", "health", "overview"]
    angle = angles[variant_idx % 5]

    # 从 commentaries 中取对应角度的解读
    angle_text = ""
    for c in commentaries:
        specific = c.get(angle, "")
        if specific and specific.strip():
            # 清理重复句
            cleaned = _dedupe_sentences(specific.strip())
            if cleaned and cleaned != xiang_core:
                angle_text = cleaned
                break

    # 没有找到角度解读时用卦辞
    if not angle_text:
        angle_text = gua_ci.strip().rstrip("。")

    # 组装：大象旨要 + 角度解读 + 收尾
    parts = []
    if xiang_core:
        parts.append(xiang_core)
    if angle_text and angle_text not in parts:
        parts.append(angle_text)
    parts.append(f"今日「{gua_name}」卦当值，当悟此理，顺势而为")

    # 用句号连接，每句以句号结尾
    result = "。".join(p for p in parts if p)
    if not result.endswith("。"):
        result += "。"
    return result


def _extract_xiang_core(da_xiang_ci):
    """从大象辞中提取核心行动指引

    大象辞格式：「象曰：[象描述]，[主语]以[行动指引]。」
    主语可能是：君子(56卦)、先王(6卦)、后(2卦)、大人(1卦)、上(1卦)
    均统一提取「[主语]以[行动指引]」部分。
    """
    if not da_xiang_ci:
        return ""
    text = da_xiang_ci.strip()
    # 去掉"象曰："前缀
    text = re.sub(r'^象曰[：:]?\s*', '', text)

    # 匹配「[主语]以[行动指引]」—— 主语可能是2-3字
    m = re.search(r'([\u4e00-\u9fff]{1,3})以(.+?)(?:[。；]|$)', text)
    if m:
        subject = m.group(1)
        action = m.group(2).strip()
        if action:
            return f"{subject}以{action}"

    # 降级：取大象辞中除象曰外的第一句
    sentences = re.split(r'[。；]', text)
    return sentences[0].strip() if sentences[0] and sentences[0].strip() else ""


def _dedupe_sentences(text):
    """去除文本中的重复句和过短句"""
    # 分句
    sentences = re.split(r'[。；，]', text)
    seen = set()
    clean = []
    for s in sentences:
        s = s.strip()
        if not s or s in seen:
            continue
        if len(s) < 3:  # 过滤太短的片段
            continue
        seen.add(s)
        clean.append(s)
    return "，".join(clean)


def _get_yi_ji_colors(gua_name, hex_data, variant_idx):
    """从 daily_fortunes.json 取宜/忌/幸运颜色

    匹配策略（确保一定能找到）：
    1. 卦名精确匹配
    2. 卦名匹配失败 → 用 hexagram_id 匹配
    3. 都失败 → 根据吉凶等级生成默认值
    """
    # 尝试匹配
    fortune_entry = None
    for entry in _DAILY_FORTUNES:
        if entry.get("hexagram_name") == gua_name:
            fortune_entry = entry
            break

    # 名称匹配失败，尝试按 id 匹配
    if fortune_entry is None:
        hex_id = hex_data.get("id")
        for entry in _DAILY_FORTUNES:
            if entry.get("hexagram_id") == hex_id:
                fortune_entry = entry
                break

    # 找到了，取变体
    if fortune_entry and fortune_entry.get("variants"):
        variants = fortune_entry["variants"]
        idx = variant_idx % len(variants)
        v = variants[idx]
        return (
            v.get("yi", ""),
            v.get("ji", ""),
            v.get("lucky_colors", []),
        )

    # 最终降级：根据吉凶等级生成默认宜忌
    level = _judge_level(gua_name)
    return _default_yi_ji(level)


def _default_yi_ji(level):
    """降级方案：根据吉凶等级生成默认宜忌"""
    if level == "吉":
        return (
            "宜：出行、签约、求职、学习新技能、拜访贵人",
            "忌：犹豫不决、错失良机、贪睡误事",
            ["红色", "黄色", "白色"],
        )
    elif level == "凶":
        return (
            "宜：静心读书、整理内务、低调行事、冥想反思",
            "忌：重大决策、冒险投资、与人争执、远行",
            ["黑色", "蓝色", "灰色"],
        )
    else:
        return (
            "宜：处理日常事务、学习充电、锻炼身体、整理收纳",
            "忌：极端行为、情绪冲动、重大改变",
            ["绿色", "白色", "黄色"],
        )


def _judge_level(gua_name):
    """根据卦名判断吉凶等级"""
    auspicious = {
        "乾", "坤", "泰", "大有", "謙", "豫", "隨", "臨", "觀",
        "賁", "復", "大畜", "頤", "咸", "恆", "晉", "家人", "益",
        "升", "鼎", "豐", "旅", "節", "中孚", "既濟",
    }
    inauspicious = {
        "否", "剝", "坎", "明夷", "蹇", "困", "革", "震", "歸妹", "未濟",
    }
    if gua_name in auspicious:
        return "吉"
    elif gua_name in inauspicious:
        return "凶"
    return "平"


def _simple_fortune(hex_data):
    """降级方案：没有 daily_fortunes.json 时的简化运势"""
    gua_name = hex_data.get("name_cn", "")
    level = _judge_level(gua_name)
    yi, ji, colors = _default_yi_ji(level)

    if level == "吉":
        fortune = "今日运势尚佳，宜积极进取，把握良机。"
    elif level == "凶":
        fortune = "今日运势有阻，宜谨慎行事，以守为攻。"
    else:
        fortune = "今日运势平稳，宜守正持中，静观其变。"

    return {
        "fortune": fortune,
        "yi": yi,
        "ji": ji,
        "lucky_colors": colors,
    }
