# -*- coding: utf-8 -*-
"""终端/服务端可视化渲染工具"""

# Unicode八卦符号
TRIGRAM_SYMBOLS = {
    "乾": "☰", "坤": "☷", "震": "☳", "巽": "☴",
    "坎": "☵", "离": "☲", "艮": "☶", "兑": "☱",
}

# 六爻线条符号
YAO_SYMBOLS = {
    6: "══  ══  老阴 (× → 阳)",
    7: "═══════  少阳",
    8: "══  ══  少阴",
    9: "═══════  老阳 (○ → 阴)",
}

# 八卦万物类象（简要）
BAGUA_NATURE = {
    "乾": "天", "坤": "地", "震": "雷", "巽": "风",
    "坎": "水", "离": "火", "艮": "山", "兑": "泽",
}


def draw_hexagram_terminal(yao_values, changing_lines, upper_name, lower_name):
    """在终端绘制卦象
    yao_values: [6,7,8,9] 从初爻到上爻的六次结果
    changing_lines: set of line indices (0-based) that are changing
    """
    lines = []
    # 从上到下显示（上爻在前）
    for i in range(5, -1, -1):
        val = yao_values[i]
        yao_num = i + 1
        marker = " ← 变爻" if i in changing_lines else ""
        if val in (7, 9):  # 阳爻
            if i in changing_lines:
                lines.append(f"  爻{yao_num}: ═══════○{marker}")
            else:
                lines.append(f"  爻{yao_num}: ═══════")
        else:  # 阴爻
            if i in changing_lines:
                lines.append(f"  爻{yao_num}: ══  ══×{marker}")
            else:
                lines.append(f"  爻{yao_num}: ══  ══")

    up_sym = TRIGRAM_SYMBOLS.get(upper_name, "?")
    lo_sym = TRIGRAM_SYMBOLS.get(lower_name, "?")

    result = f"""
  ┌────────────────────┐
  │  {up_sym} {upper_name}上  {lo_sym} {lower_name}下  │
  ├────────────────────┤
""" + "\n".join(lines) + f"""
  └────────────────────┘"""
    return result


def draw_bagua_diagram():
    """返回八卦图ASCII art"""
    return """
        ☰ 乾 (天)
    ☴ 巽    ☵ 坎    ☶ 艮
  (风)     (水)     (山)

    ☲ 离    ☳ 震    ☱ 兑
  (火)     (雷)     (泽)

        ☷ 坤 (地)
"""


def format_wuxing_balance(counts):
    """格式化五行分布"""
    bars = {}
    wuxing_names = {"木": "木", "火": "火", "土": "土", "金": "金", "水": "水"}
    max_count = max(counts.values()) if counts else 1
    for wx, cnt in counts.items():
        bar_len = int(cnt / max_count * 10) if max_count > 0 else 0
        bars[wx] = "█" * bar_len + "░" * (10 - bar_len)

    lines = []
    for wx in ["木", "火", "土", "金", "水"]:
        cnt = counts.get(wx, 0)
        lines.append(f"  {wx}: {bars.get(wx, '')}  ({cnt})")
    return "\n".join(lines)
