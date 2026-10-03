# -*- coding: utf-8 -*-
"""节气工具模块 - 计算节气、养生建议、开运提示"""

from datetime import date

from utils import xuanji_date

# 24节气数据（简化版：使用近似日期）
# 实际节气时间每年略有浮动，这里取常见日期
JIEQI_DATES = [
    ("小寒", 1, 5), ("大寒", 1, 20),
    ("立春", 2, 4), ("雨水", 2, 19),
    ("惊蛰", 3, 6), ("春分", 3, 21),
    ("清明", 4, 5), ("谷雨", 4, 20),
    ("立夏", 5, 6), ("小满", 5, 21),
    ("芒种", 6, 6), ("夏至", 6, 21),
    ("小暑", 7, 7), ("大暑", 7, 23),
    ("立秋", 8, 8), ("处暑", 8, 23),
    ("白露", 9, 8), ("秋分", 9, 23),
    ("寒露", 10, 8), ("霜降", 10, 23),
    ("立冬", 11, 7), ("小雪", 11, 22),
    ("大雪", 12, 7), ("冬至", 12, 22),
]

# 节气养生建议和开运提示
JIEQI_INFO = {
    "立春": {
        "wuxing": "木",
        "direction": "东方",
        "health": "养肝护阳，宜食辛温发散之品，忌酸收",
        "fortune": "万物始生，宜谋新事，东方求财最旺",
        "color": "青色、绿色",
        "emoji": "🌱"
    },
    "雨水": {
        "wuxing": "木",
        "direction": "东方",
        "health": "春寒料峭，防湿健脾，少食生冷",
        "fortune": "雨润万物，宜播种希望，东南方位吉",
        "color": "青色、绿色",
        "emoji": "🌧️"
    },
    "惊蛰": {
        "wuxing": "木",
        "direction": "东方",
        "health": "春雷惊百虫，养肝舒筋，多食绿叶蔬菜",
        "fortune": "雷动阳气，宜动不宜静，主动出击可成",
        "color": "青色、绿色",
        "emoji": "⚡"
    },
    "春分": {
        "wuxing": "木",
        "direction": "正东",
        "health": "阴阳平衡，调和气血，宜平补",
        "fortune": "昼夜均分，宜守中道，合作共赢",
        "color": "青色、绿色",
        "emoji": "⚖️"
    },
    "清明": {
        "wuxing": "木",
        "direction": "东方",
        "health": "清气上升，养肝明目，忌动肝火",
        "fortune": "清明时节，祭祖缅怀，家运亨通",
        "color": "青色、绿色",
        "emoji": "🍃"
    },
    "谷雨": {
        "wuxing": "土",
        "direction": "东南",
        "health": "雨生百谷，健脾祛湿，少食肥甘",
        "fortune": "播种收获季，付出必有回报",
        "color": "黄色、棕色",
        "emoji": "🌾"
    },
    "立夏": {
        "wuxing": "火",
        "direction": "南方",
        "health": "养心安神，清淡饮食，忌大汗伤阳",
        "fortune": "火气当令，事业运旺，南方求财吉",
        "color": "红色、紫色",
        "emoji": "☀️"
    },
    "小满": {
        "wuxing": "火",
        "direction": "南方",
        "health": "小满未满，防暑祛湿，忌贪凉",
        "fortune": "小得盈满，宜积累勿急，稳步上升",
        "color": "红色、紫色",
        "emoji": "🌻"
    },
    "芒种": {
        "wuxing": "火",
        "direction": "南方",
        "health": "养心益气，清热消暑，宜午休",
        "fortune": "忙碌播种时，付出终有收获",
        "color": "红色、紫色",
        "emoji": "🌾"
    },
    "夏至": {
        "wuxing": "火",
        "direction": "正南",
        "health": "阳极阴生，养心护阳，清补为主",
        "fortune": "阳气最盛，宜扬名立万，忌冲动",
        "color": "红色、紫色",
        "emoji": "🔥"
    },
    "小暑": {
        "wuxing": "火",
        "direction": "南方",
        "health": "小暑大暑，防暑降火，多饮温水",
        "fortune": "暑气渐盛，宜静不宜动，守业为上",
        "color": "红色、紫色",
        "emoji": "🌡️"
    },
    "大暑": {
        "wuxing": "土",
        "direction": "中央",
        "health": "暑湿交蒸，健脾祛湿，清淡为宜",
        "fortune": "酷暑难耐，宜养精蓄锐，待时而动",
        "color": "黄色、棕色",
        "emoji": "🌤️"
    },
    "立秋": {
        "wuxing": "金",
        "direction": "西方",
        "health": "养肺润燥，少辛增酸，防秋燥",
        "fortune": "秋收之始，收获在即，西方财运旺",
        "color": "白色、金色",
        "emoji": "🍂"
    },
    "处暑": {
        "wuxing": "金",
        "direction": "西方",
        "health": "暑气渐退，滋阴润肺，忌贪凉",
        "fortune": "暑去凉来，宜收尾项目，整理得失",
        "color": "白色、金色",
        "emoji": "🌬️"
    },
    "白露": {
        "wuxing": "金",
        "direction": "西方",
        "health": "白露身不露，添衣保暖，养肺为要",
        "fortune": "露凝成白，收获季节，守财为上",
        "color": "白色、金色",
        "emoji": "💧"
    },
    "秋分": {
        "wuxing": "金",
        "direction": "正西",
        "health": "阴阳平分，调养身心，温补为宜",
        "fortune": "昼夜均衡，宜守正中，合作共赢",
        "color": "白色、金色",
        "emoji": "⚖️"
    },
    "寒露": {
        "wuxing": "金",
        "direction": "西方",
        "health": "寒露寒露，防寒保暖，养肺润燥",
        "fortune": "寒气渐生，宜收敛锋芒，蓄势待发",
        "color": "白色、金色",
        "emoji": "🍁"
    },
    "霜降": {
        "wuxing": "土",
        "direction": "西北",
        "health": "霜降见霜，温补脾胃，防寒保暖",
        "fortune": "秋末冬初，宜总结复盘，规划来年",
        "color": "黄色、棕色",
        "emoji": "❄️"
    },
    "立冬": {
        "wuxing": "水",
        "direction": "北方",
        "health": "养肾藏精，温补为主，早睡晚起",
        "fortune": "冬藏之始，宜蓄势养精，北方求财",
        "color": "黑色、蓝色",
        "emoji": "🌨️"
    },
    "小雪": {
        "wuxing": "水",
        "direction": "北方",
        "health": "小雪封地，温补肾阳，防寒保暖",
        "fortune": "雪降藏机，宜静不宜动，谋划为先",
        "color": "黑色、蓝色",
        "emoji": "🌨️"
    },
    "大雪": {
        "wuxing": "水",
        "direction": "北方",
        "health": "大雪进补，滋阴补阳，宜温热食物",
        "fortune": "大雪封山，宜藏不宜露，积蓄实力",
        "color": "黑色、蓝色",
        "emoji": "❄️"
    },
    "冬至": {
        "wuxing": "水",
        "direction": "正北",
        "health": "阴极阳生，大补元气，一阳来复",
        "fortune": "冬至大如年，阴极阳生，转运之始",
        "color": "黑色、蓝色",
        "emoji": "🌑"
    },
    "小寒": {
        "wuxing": "水",
        "direction": "北方",
        "health": "小寒大寒，防寒保暖，温补肾阳",
        "fortune": "寒气袭人，宜守不宜攻，耐心等待",
        "color": "黑色、蓝色",
        "emoji": "🧊"
    },
    "大寒": {
        "wuxing": "土",
        "direction": "中央",
        "health": "大寒迎春，固护脾胃，为来年储能",
        "fortune": "大寒至，春将至，宜辞旧迎新",
        "color": "黄色、棕色",
        "emoji": "🌑"
    },
}


def get_current_jieqi(d=None):
    """获取当前节气信息

    返回: {
        "name": "立春",
        "date": date(2026, 2, 4),
        "days_ago": 5,  # 距离该节气已过去5天
        "next_name": "雨水",
        "next_date": date(2026, 2, 19),
        "days_until": 10,  # 距离下个节气还有10天
        "is_jieqi_day": False,  # 今天是否正好是节气日
        "info": {...}  # 节气详细信息
    }
    """
    if d is None:
        d = xuanji_date()

    year = d.year

    # 构建本年度所有节气的日期
    jieqi_list = []
    for name, month, day in JIEQI_DATES:
        try:
            jq_date = date(year, month, day)
            jieqi_list.append((name, jq_date))
        except ValueError:
            # 处理闰年等特殊情况
            pass

    # 加上明年的前几个节气（处理跨年）
    for name, month, day in JIEQI_DATES[:3]:
        try:
            jq_date = date(year + 1, month, day)
            jieqi_list.append((name, jq_date))
        except ValueError:
            pass

    # 找到当前节气（最近的过去的节气）
    current_jq = None
    next_jq = None

    for i, (name, jq_date) in enumerate(jieqi_list):
        if jq_date <= d:
            current_jq = (name, jq_date)
            if i + 1 < len(jieqi_list):
                next_jq = jieqi_list[i + 1]
        else:
            if next_jq is None:
                next_jq = (name, jq_date)
            break

    # 如果没找到当前节气（日期早于当年第一个节气）
    if current_jq is None:
        # 使用去年最后一个节气
        name, month, day = JIEQI_DATES[-1]
        current_jq = (name, date(year - 1, month, day))

    # 如果没找到下一个节气
    if next_jq is None:
        name, month, day = JIEQI_DATES[0]
        next_jq = (name, date(year + 1, month, day))

    current_name, current_date = current_jq
    next_name, next_date = next_jq

    days_ago = (d - current_date).days
    days_until = (next_date - d).days
    is_jieqi_day = (d == current_date)

    return {
        "name": current_name,
        "date": current_date,
        "days_ago": days_ago,
        "next_name": next_name,
        "next_date": next_date,
        "days_until": days_until,
        "is_jieqi_day": is_jieqi_day,
        "info": JIEQI_INFO.get(current_name, {}),
        "next_info": JIEQI_INFO.get(next_name, {}),
    }


def format_jieqi_card(jieqi_data):
    """格式化节气卡片数据，供模板使用

    只在节气当天返回数据，其他日子返回 None

    返回: {
        "title": "今日节气：立春 🌱",
        "greeting": "立春至，万物始生...",
        "health": "养肝护阳，宜食辛温发散之品，忌酸收",
        "fortune": "万物始生，宜谋新事，东方求财最旺",
        "wuxing": "木",
        "direction": "东方",
        "color": "青色、绿色",
        "emoji": "🌱"
    } 或 None
    """
    # 只在节气当天显示
    if not jieqi_data["is_jieqi_day"]:
        return None

    name = jieqi_data["name"]
    info = jieqi_data["info"]
    emoji = info.get("emoji", "🌿")

    return {
        "title": f"今日节气：{name} {emoji}",
        "greeting": f"今日正值{name}，天地交泰，万象更新。道友当顺应天时，趋吉避凶。",
        "health": info.get("health", ""),
        "fortune": info.get("fortune", ""),
        "wuxing": info.get("wuxing", ""),
        "direction": info.get("direction", ""),
        "color": info.get("color", ""),
        "emoji": emoji,
        "name": name,
    }
