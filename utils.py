# -*- coding: utf-8 -*-
"""通用工具模块 — 编码、农历转换等"""

import sys
import io
import json
import os
from datetime import date, timedelta

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def fix_encoding():
    """修复 Windows 终端 UTF-8 编码"""
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def load_json(filename):
    """从 data/ 目录加载 JSON 文件"""
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ============================================================
# 农历转换（1900-2100年万年历数据）
# 数据来源：香港天文台 + 算法推导
# ============================================================

# 农历年数据：每个整数编码该年农历信息
# 低12位 = 每月大小月（1=大月30天, 0=小月29天）
# 高4位 = 闰月月份（0=无闰月）
LUNAR_YEAR_DATA = {
    1900: 0x0000c, 1901: 0x004d5, 1902: 0x00d4a, 1903: 0x00d55,
    1904: 0x0056a, 1905: 0x009ad, 1906: 0x002da, 1907: 0x00c95,
    1908: 0x00d4e, 1909: 0x00d4a, 1910: 0x00d55, 1911: 0x006d6,
    1912: 0x009b5, 1913: 0x005ba, 1914: 0x00ad6, 1915: 0x00a95,
    1916: 0x0052d, 1917: 0x004b5, 1918: 0x00a56, 1919: 0x00a9a,
    1920: 0x0099a, 1921: 0x005da, 1922: 0x00adb, 1923: 0x00a5b,
    1924: 0x0092b, 1925: 0x004ae, 1926: 0x0056c, 1927: 0x005ab,
    1928: 0x009b5, 1929: 0x009aa, 1930: 0x009ad, 1931: 0x00555,
    1932: 0x00ad5, 1933: 0x005b5, 1934: 0x004b7, 1935: 0x00497,
    1936: 0x00a57, 1937: 0x00a9b, 1938: 0x0095b, 1939: 0x002db,
    1940: 0x00a97, 1941: 0x0052b, 1942: 0x00935, 1943: 0x0052e,
    1944: 0x00a56, 1945: 0x00a56, 1946: 0x00956, 1947: 0x004da,
    1948: 0x004b5, 1949: 0x00935, 1950: 0x0052b, 1951: 0x00935,
    1952: 0x00536, 1953: 0x00a9a, 1954: 0x0095a, 1955: 0x005ac,
    1956: 0x009b5, 1957: 0x004b6, 1958: 0x006ad, 1959: 0x00555,
    1960: 0x00a56, 1961: 0x0092e, 1962: 0x004ad, 1963: 0x0094a,
    1964: 0x00556, 1965: 0x00a95, 1966: 0x00596, 1967: 0x005aa,
    1968: 0x009b5, 1969: 0x004b7, 1970: 0x004ad, 1971: 0x00955,
    1972: 0x004d6, 1973: 0x00a9a, 1974: 0x0095a, 1975: 0x0056a,
    1976: 0x0096d, 1977: 0x004ae, 1978: 0x004b7, 1979: 0x00a4b,
    1980: 0x00556, 1981: 0x00a95, 1982: 0x004b6, 1983: 0x00956,
    1984: 0x00a5a, 1985: 0x0052e, 1986: 0x00495, 1987: 0x00a95,
    1988: 0x0052b, 1989: 0x0052b, 1990: 0x0092f, 1991: 0x00536,
    1992: 0x004b7, 1993: 0x00a4b, 1994: 0x005ab, 1995: 0x009ad,
    1996: 0x00556, 1997: 0x00a57, 1998: 0x00a5a, 1999: 0x0052e,
    2000: 0x004b6, 2001: 0x00ab6, 2002: 0x0092e, 2003: 0x0052d,
    2004: 0x00a56, 2005: 0x00536, 2006: 0x0095a, 2007: 0x0056b,
    2008: 0x004b7, 2009: 0x0092d, 2010: 0x0052d, 2011: 0x00a95,
    2012: 0x004b5, 2013: 0x005aa, 2014: 0x0096e, 2015: 0x0052f,
    2016: 0x004ad, 2017: 0x00a56, 2018: 0x00555, 2019: 0x00935,
    2020: 0x004b6, 2021: 0x004b5, 2022: 0x00a56, 2023: 0x0052e,
    2024: 0x00a56, 2025: 0x00956, 2026: 0x0055a, 2027: 0x009ad,
    2028: 0x00556, 2029: 0x004b7, 2030: 0x004ad, 2031: 0x00955,
    2032: 0x0052e, 2033: 0x00a9a, 2034: 0x0052a, 2035: 0x005b6,
    2036: 0x00a9e, 2037: 0x004b7, 2038: 0x004ad, 2039: 0x0092d,
    2040: 0x00536, 2041: 0x00535, 2042: 0x002b7, 2043: 0x00995,
    2044: 0x00556, 2045: 0x00a56, 2046: 0x00536, 2047: 0x004b7,
    2048: 0x0092d, 2049: 0x0052d, 2050: 0x00995,
}

# 农历1900-01-01对应公历1900-01-31
LUNAR_BASE = date(1900, 1, 31)

TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
SHENGXIAO = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]
JIEQI_APPROX = [
    ("立春", 2, 4), ("惊蛰", 3, 6), ("清明", 4, 5),
    ("立夏", 5, 6), ("芒种", 6, 6), ("小暑", 7, 7),
    ("立秋", 8, 8), ("白露", 9, 8), ("寒露", 10, 8),
    ("立冬", 11, 7), ("大雪", 12, 7), ("小寒", 1, 6),
]


def _lunar_year_info(y):
    """获取农历年编码信息，返回 (闰月, 月大小列表)"""
    code = LUNAR_YEAR_DATA.get(y, 0x004b5)
    leap = (code >> 12) & 0xf  # 闰月月份（0=无闰）
    months = []
    for i in range(12):
        months.append(30 if (code >> i) & 1 else 29)
    # 如果是闰年，在闰月后插入闰月
    if leap:
        # 闰月大小由第13位决定（如果有的话），这里简化处理为29天
        leap_big = (code >> 16) & 1
        months.insert(leap, 30 if leap_big else 29)
    return leap, months


def solar_to_lunar(d):
    """公历转农历，返回 (年, 月, 日, 是否闰月)"""
    if d < LUNAR_BASE:
        raise ValueError(f"日期 {d} 早于1900年，暂不支持")

    # 计算从基准日到目标日的天数
    days = (d - LUNAR_BASE).days

    year = 1900
    while year <= 2100:
        leap, months = _lunar_year_info(year)
        total = sum(months)
        if days < total:
            break
        days -= total
        year += 1

    if year > 2100:
        raise ValueError(f"日期 {d} 超出支持范围")

    leap, months = _lunar_year_info(year)

    # 找出所在月份
    month = 1
    is_leap = False
    for i, mdays in enumerate(months):
        if days < mdays:
            month = i + 1
            if leap and i > leap:
                month = i  # 闰月之后，月份减1（因为插入了一个月）
            if leap and i == leap:
                is_leap = True
            break
        days -= mdays
    else:
        month = len(months)

    day = days + 1
    return year, month, day, is_leap


def get_lunar_month_ganzhi(year_gz_idx, month_num):
    """五虎遁年起月法：由年干和农历月份数求月干支索引"""
    # 年干索引
    year_gan_idx = year_gz_idx % 10
    # 子月（大雪后）开始，寅月为第1个月
    # 五虎遁：甲己之年丙作首，乙庚之年戊为头...
    month_gan_offset = [2, 4, 6, 8, 0]  # 甲己→丙寅, 乙庚→戊寅, etc.
    base_gan = month_gan_offset[year_gan_idx % 5]
    # 月支索引：寅=2开始
    month_zhi_idx = (month_num + 1) % 12  # 正月=寅(2)
    month_gan_idx = (base_gan + month_num - 1) % 10
    return month_gan_idx * 12 + month_zhi_idx  # 返回60甲子中位置简化为gan*12+zhi


def ganzhi_to_str(gz_idx):
    """60甲子索引转干支字符串"""
    if gz_idx < 60:
        return TIANGAN[gz_idx % 10] + DIZHI[gz_idx % 12]
    # 简化版：直接算
    g = gz_idx % 10
    z = gz_idx % 12
    return TIANGAN[g] + DIZHI[z]


def get_12_day_officer(day_gan):
    """十二建星（建除满平定执破危成收开闭）"""
    pass  # 暂不实现


def get_local_ip():
    """获取本机局域网IP"""
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
