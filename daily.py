# -*- coding: utf-8 -*-
"""每日运势引擎 — 基于日期计算当日卦象和运势"""

import hashlib
from datetime import date
from utils import load_json, TIANGAN, DIZHI

_HEXAGRAMS = None


def _load():
    global _HEXAGRAMS
    if _HEXAGRAMS is None:
        _HEXAGRAMS = load_json('hexagrams.json')


def daily_hexagram(d=None):
    """根据日期计算当日卦象（MD5(date) % 64 + 1）"""
    if d is None:
        d = date.today()
    day_str = d.isoformat()
    hash_val = int(hashlib.md5(day_str.encode()).hexdigest(), 16)
    idx = (hash_val % 64) + 1

    _load()
    for key, hex_data in _HEXAGRAMS.items():
        if hex_data["id"] == idx:
            return hex_data, key
    return None, None


def daily_ganzhi(d=None):
    """计算当日干支（简化版：以1900-01-01甲戌日为基准）"""
    if d is None:
        d = date.today()
    base = date(1900, 1, 1)
    base_gz = 10  # 1900-01-01是甲戌日（甲戌在60甲子中排第11，0-based=10）
    days_diff = (d - base).days
    gz_idx = (base_gz + days_diff) % 60
    gan = TIANGAN[gz_idx % 10]
    zhi = DIZHI[gz_idx % 12]
    return gan + zhi, gz_idx


def daily_fortune(d=None):
    """生成每日综合运势"""
    if d is None:
        d = date.today()

    hex_data, key = daily_hexagram(d)
    gz_str, gz_idx = daily_ganzhi(d)

    if not hex_data:
        return {"error": "无法获取今日卦象"}

    # 从卦象提取运势
    gua_name = hex_data["name_cn"]
    da_xiang = hex_data.get("da_xiang_ci", "")

    # 根据卦名简单判断吉凶
    auspicious_hexagrams = {
        "乾", "坤", "泰", "大有", "谦", "豫", "随", "临", "观",
        "贲", "复", "大畜", "颐", "咸", "恒", "晋", "家人", "益",
        "升", "鼎", "丰", "旅", "节", "中孚", "既济",
    }
    inauspicious_hexagrams = {
        "否", "剥", "坎", "明夷", "蹇", "困", "革", "震", "归妹", "未济",
    }

    if gua_name in auspicious_hexagrams:
        level = "吉"
        fortune = "今日运势尚佳，宜积极进取，把握良机。"
    elif gua_name in inauspicious_hexagrams:
        level = "凶"
        fortune = "今日运势有阻，宜谨慎行事，以守为攻。退一步海阔天空。"
    else:
        level = "中"
        fortune = "今日运势平稳，吉凶参半。宜守正持中，静观其变。"

    return {
        "date": d.isoformat(),
        "day_ganzhi": gz_str,
        "hexagram": hex_data,
        "hexagram_key": key,
        "level": level,
        "fortune": fortune,
        "da_xiang": da_xiang,
    }
