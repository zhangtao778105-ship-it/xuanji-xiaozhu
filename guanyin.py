# -*- coding: utf-8 -*-
"""观音灵签引擎 — 抽签、掷筊确认"""

import random
from utils import load_json

_LOTS = None


def _load():
    global _LOTS
    if _LOTS is None:
        _LOTS = load_json('guanyin_lots.json')


def draw_lot():
    """随机抽取1签（1-100）"""
    _load()
    idx = random.randint(0, 99)
    return _LOTS[idx]


def toss_jiaobei():
    """
    掷筊：模拟两片筊杯
    返回 "圣杯"(一正一反) / "笑杯"(两正) / "阴杯"(两反)
    """
    p1 = random.choice(["正", "反"])
    p2 = random.choice(["正", "反"])
    if p1 != p2:
        return "圣杯", f"一{p1}一反 — 圣杯！观音菩萨应允了。"
    elif p1 == "正":
        return "笑杯", "两面皆正 — 笑杯。菩萨笑而不答，请再掷一次。"
    else:
        return "阴杯", "两面皆反 — 阴杯。菩萨未允，此签恐非天意。"


def full_draw():
    """
    完整抽签流程
    返回: {lot, jiaobei_result, confirmed, attempts}
    """
    _load()
    lot = draw_lot()
    max_attempts = 3
    results = []

    for attempt in range(max_attempts):
        result, msg = toss_jiaobei()
        results.append({"result": result, "message": msg})
        if result == "圣杯":
            confirmed = True
            confirmed_msg = ""
            break
    else:
        confirmed = False
        confirmed_msg = "三次未得圣杯，此签仅供参考。"

    # AI 深度解读（可插拔）
    ai_commentary = None
    try:
        from ai_interpreter import get_interpreter
        ai = get_interpreter()
        if ai.enabled:
            ai_data = {
                "lot": lot,
                "confirmed": confirmed,
            }
            ai_commentary = ai.interpret("guanyin", ai_data)
    except Exception:
        pass

    # AI 不可用时，从静态语料库随机选取判词和解读变体
    static_judgment = None
    static_interpretation = None
    if not ai_commentary:
        judgments = lot.get("judgments", [])
        if judgments:
            static_judgment = random.choice(judgments)
        variants = lot.get("interpretation_variants", [])
        if variants:
            static_interpretation = random.choice(variants)

    result_data = {
        "lot": lot,
        "jiaobei_results": results,
        "confirmed": confirmed,
        "attempts": min(attempt + 1, max_attempts),
        "ai_commentary": ai_commentary,
        "static_judgment": static_judgment,
        "static_interpretation": static_interpretation,
    }
    if not confirmed:
        result_data["note"] = confirmed_msg
    return result_data
