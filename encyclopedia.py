# -*- coding: utf-8 -*-
"""玄学百科引擎 — 综合知识库查询与搜索"""

from utils import load_json

_ENCYCLOPEDIA = None


def _load():
    global _ENCYCLOPEDIA
    if _ENCYCLOPEDIA is None:
        _ENCYCLOPEDIA = load_json('encyclopedia.json')


def get_categories():
    """获取所有百科分类"""
    _load()
    return list(_ENCYCLOPEDIA.keys())


def get_category(cat_name):
    """获取特定分类的内容"""
    _load()
    return _ENCYCLOPEDIA.get(cat_name)


def get_topic(cat_name, topic_name):
    """获取特定主题"""
    _load()
    cat = _ENCYCLOPEDIA.get(cat_name, {})
    if isinstance(cat, dict):
        return cat.get(topic_name)
    return None


def get_bagua():
    """获取八卦信息"""
    _load()
    zhouyi = _ENCYCLOPEDIA.get("周易", {})
    return zhouyi.get("八卦", {})


def get_wuxing():
    """获取五行信息"""
    _load()
    return _ENCYCLOPEDIA.get("五行", {})


def get_tiangan_dizhi():
    """获取天干地支信息"""
    _load()
    return _ENCYCLOPEDIA.get("天干地支", {})


def get_qimen():
    """获取奇门遁甲信息"""
    _load()
    return _ENCYCLOPEDIA.get("奇门遁甲", {})


def get_meihua():
    """获取梅花易数信息"""
    _load()
    return _ENCYCLOPEDIA.get("梅花易数", {})


def get_mianxiang():
    """获取面相手相信息"""
    _load()
    return _ENCYCLOPEDIA.get("面相手相", {})


def search(query):
    """全局模糊搜索玄学百科"""
    _load()
    results = []

    def _search_dict(d, cat="", path=""):
        if isinstance(d, dict):
            for k, v in d.items():
                current_path = f"{path} > {k}" if path else f"{cat} > {k}"
                if query in str(k):
                    preview = str(v)[:200] if not isinstance(v, dict) else "(有子分类)"
                    results.append({"category": cat, "path": current_path, "content": preview})
                if isinstance(v, dict):
                    _search_dict(v, cat, current_path)
                elif isinstance(v, str) and query in v:
                    results.append({"category": cat, "path": current_path, "content": v[:200]})
                elif isinstance(v, list):
                    for item in v:
                        if query in str(item):
                            results.append({"category": cat, "path": current_path, "content": str(item)[:200]})

    for cat_name, cat_content in _ENCYCLOPEDIA.items():
        _search_dict(cat_content, cat_name, cat_name)

    return results
