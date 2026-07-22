# -*- coding: utf-8 -*-
"""周易金钱卦引擎 — 铜钱起卦、变卦、解卦"""

import random
from utils import load_json

# 加载数据
_HEXAGRAMS = None
_TRIGRAMS = None


def _load():
    global _HEXAGRAMS, _TRIGRAMS
    if _HEXAGRAMS is None:
        _HEXAGRAMS = load_json('hexagrams.json')
    if _TRIGRAMS is None:
        _TRIGRAMS = load_json('trigram_map.json')


def toss_once():
    """
    模拟三枚铜钱掷一次
    三枚铜钱，正面(阳)为3分，背面(阴)为2分
    返回: 6=老阴, 7=少阳, 8=少阴, 9=老阳
    """
    coins = [random.choice([2, 3]) for _ in range(3)]
    total = sum(coins)
    # 6(2+2+2)老阴, 7(2+2+3)少阳, 8(2+3+3)少阴, 9(3+3+3)老阳
    # 概率: 老阴=1/8, 少阳=3/8, 少阴=3/8, 老阳=1/8
    return total


def toss_six():
    """掷六次，返回 (yao_values, changing_lines)
    yao_values: [6,7,8,9] 从初爻(0)到上爻(5)
    changing_lines: set of indices where yao is 6 or 9
    """
    values = [toss_once() for _ in range(6)]
    changing = {i for i, v in enumerate(values) if v in (6, 9)}
    return values, changing


def values_to_binary(values):
    """将六次结果转为二进制key（从下往上，1=阳0=阴）"""
    # 值7,9为阳爻 -> '1'；值6,8为阴爻 -> '0'
    return ''.join('1' if v in (7, 9) else '0' for v in values)


def get_hexagram(binary_key):
    """根据二进制key获取卦数据"""
    _load()
    return _HEXAGRAMS.get(binary_key)


def get_trigram(name):
    """根据卦名获取八卦信息"""
    _load()
    return _TRIGRAMS.get(name)


def get_trigram_by_binary(bin3):
    """根据3位二进制获取八卦信息"""
    _load()
    for key, val in _TRIGRAMS.items():
        if key == bin3:
            return val
    return None


def calc_changed_hexagram(values, changing):
    """计算变卦的六爻值"""
    changed = list(values)
    for i in changing:
        if changed[i] == 6:  # 老阴 → 少阳
            changed[i] = 7
        elif changed[i] == 9:  # 老阳 → 少阴
            changed[i] = 8
    return changed


def interpret(original_key, changed_key, changing_lines):
    """
    解卦（朱熹《易学启蒙》规则）
    返回 dict: {method, original, changed, interpretations}
    """
    _load()
    orig = _HEXAGRAMS.get(original_key)
    changed = _HEXAGRAMS.get(changed_key)
    if not orig:
        return {"error": f"未找到卦象: {original_key}"}

    num_changing = len(changing_lines)

    result = {
        "original": orig,
        "changed": changed if num_changing > 0 else None,
        "num_changing": num_changing,
        "changing_lines": sorted(changing_lines),
        "method": "",
        "interpretations": [],
    }

    if num_changing == 0:
        result["method"] = "静卦 — 以本卦卦辞为主"
        result["interpretations"].append({
            "source": f"本卦·{orig['name_cn']}卦辞",
            "text": orig["gua_ci"],
        })
        if orig.get("tuan_ci"):
            result["interpretations"].append({
                "source": "彖辞",
                "text": orig["tuan_ci"],
            })
        if orig.get("da_xiang_ci"):
            result["interpretations"].append({
                "source": "大象辞",
                "text": orig["da_xiang_ci"],
            })

    elif num_changing == 1:
        idx = list(changing_lines)[0]
        result["method"] = f"一变爻 — 以本卦第{idx+1}爻（{_yao_name(idx, values=None)}）爻辞为主"
        result["interpretations"].append({
            "source": f"本卦·{orig['name_cn']}·{_yao_name(idx, values=None)}",
            "text": orig["yao_ci"][idx],
        })

    elif num_changing == 2:
        idxs = sorted(changing_lines)
        result["method"] = f"二变爻 — 以两变爻爻辞参断，以上爻（第{idxs[1]+1}爻）为主"
        for idx in idxs:
            result["interpretations"].append({
                "source": f"本卦·{orig['name_cn']}·{_yao_name(idx, values=None)}",
                "text": orig["yao_ci"][idx],
            })

    elif num_changing == 3:
        result["method"] = "三变爻 — 参看本卦与变卦卦辞"
        result["interpretations"].append({
            "source": f"本卦·{orig['name_cn']}卦辞",
            "text": orig["gua_ci"],
        })
        if changed:
            result["interpretations"].append({
                "source": f"变卦·{changed['name_cn']}卦辞",
                "text": changed["gua_ci"],
            })

    elif num_changing == 4:
        unchanged = [i for i in range(6) if i not in changing_lines]
        result["method"] = f"四变爻 — 以变卦中不变爻辞为主，以下爻为主"
        for idx in unchanged:
            if changed:
                result["interpretations"].append({
                    "source": f"变卦·{changed['name_cn']}·{_yao_name(idx, values=None)}",
                    "text": changed["yao_ci"][idx],
                })

    elif num_changing == 5:
        unchanged = [i for i in range(6) if i not in changing_lines]
        idx = unchanged[0]
        result["method"] = f"五变爻 — 以变卦中不变之爻辞为主"
        if changed:
            result["interpretations"].append({
                "source": f"变卦·{changed['name_cn']}·{_yao_name(idx, values=None)}",
                "text": changed["yao_ci"][idx],
            })

    elif num_changing == 6:
        result["method"] = "六爻皆变 — "
        if original_key == "111111":  # 乾卦
            result["method"] += "用九"
            result["interpretations"].append({
                "source": "乾·用九",
                "text": orig.get("yong_jiu", "见群龙无首，吉。"),
            })
        elif original_key == "000000":  # 坤卦
            result["method"] += "用六"
            result["interpretations"].append({
                "source": "坤·用六",
                "text": orig.get("yong_liu", "利永贞。"),
            })
        else:
            result["method"] += "以变卦卦辞为主"
            if changed:
                result["interpretations"].append({
                    "source": f"变卦·{changed['name_cn']}卦辞",
                    "text": changed["gua_ci"],
                })

    return result


def _yao_name(idx, values=None):
    """获取爻的称谓（初九、六二等）"""
    yin_yang_words = {7: "九", 9: "九", 6: "六", 8: "六"}
    pos_names = {0: "初", 1: "二", 2: "三", 3: "四", 4: "五", 5: "上"}
    # 简化：用位置名+阴/阳
    if values and idx < len(values):
        yy = yin_yang_words.get(values[idx], "九")
    else:
        yy = "九"
    return f"{pos_names[idx]}{yy}"


def _do_reading(values, changing):
    """内部：给定爻值和变爻，完成解卦+AI+静态解读"""
    orig_key = values_to_binary(values)
    changed_vals = calc_changed_hexagram(values, changing)
    changed_key = values_to_binary(changed_vals)

    interpretation = interpret(orig_key, changed_key, changing)

    # AI 深度解读（可插拔）
    ai_commentary = None
    try:
        from ai_interpreter import get_interpreter
        ai = get_interpreter()
        if ai.enabled:
            orig = interpretation.get("original", {})
            changed = interpretation.get("changed", {})
            ai_data = {
                "original_hexagram": {
                    "name_cn": orig.get("name_cn", ""),
                    "upper_trigram": orig.get("upper_trigram", ""),
                    "lower_trigram": orig.get("lower_trigram", ""),
                    "gua_ci": orig.get("gua_ci", ""),
                },
                "changed_hexagram": {
                    "name_cn": changed.get("name_cn", ""),
                } if changed else None,
                "changing_lines": sorted(changing) if changing else [],
                "num_changing": len(changing) if changing else 0,
                "method": interpretation.get("method", ""),
                "interpretations": interpretation.get("interpretations", []),
            }
            ai_commentary = ai.interpret("iching", ai_data)
    except Exception:
        pass

    # AI 不可用时，加载本卦的白话点评
    static_commentary = None
    if not ai_commentary:
        static_commentary = _load_commentary(orig_key)

    return {
        "yao_values": values,
        "changing_lines": list(changing),
        "original_key": orig_key,
        "changed_key": changed_key if changing else None,
        "interpretation": interpretation,
        "ai_commentary": ai_commentary,
        "static_commentary": static_commentary,
    }


def full_reading():
    """完整起卦流程（随机掷币），返回前端需要的所有数据"""
    values, changing = toss_six()
    return _do_reading(values, changing)


def full_reading_from_values(values):
    """
    根据前端传入的六爻值起卦（跳过随机掷币）
    values: [6,7,8,9] × 6，从初爻(0)到上爻(5)
    """
    values = [int(v) for v in values]
    if len(values) != 6 or any(v not in (6, 7, 8, 9) for v in values):
        raise ValueError(f"爻值必须为6个[6,7,8,9]，收到: {values}")
    changing = {i for i, v in enumerate(values) if v in (6, 9)}
    return _do_reading(values, changing)


# 白话点评缓存
_commentaries_cache = None


def _load_commentary(binary_key):
    """加载本卦的白话点评（道长口吻，单段文字）"""
    global _commentaries_cache
    import os
    if _commentaries_cache is None:
        path = os.path.join(os.path.dirname(__file__), 'data', 'hexagram_commentaries.json')
        if os.path.exists(path):
            import json
            with open(path, 'r', encoding='utf-8') as f:
                _commentaries_cache = json.load(f)
        else:
            _commentaries_cache = {}
    return _commentaries_cache.get(binary_key)
