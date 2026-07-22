# -*- coding: utf-8 -*-
"""风水百科引擎 — 知识库查询"""

from utils import load_json

_FENGSHUI = None


def _load():
    global _FENGSHUI
    if _FENGSHUI is None:
        _FENGSHUI = load_json('fengshui.json')


def get_bazhai():
    """获取八宅风水"""
    _load()
    return _FENGSHUI.get("八宅", {})


def get_xuankong():
    """获取玄空飞星"""
    _load()
    return _FENGSHUI.get("玄空飞星", {})


def get_xingfa():
    """获取形法风水（龙穴砂水向）"""
    _load()
    return _FENGSHUI.get("形法", {})


def get_shaqi():
    """获取煞气列表"""
    _load()
    return _FENGSHUI.get("煞气", {})


def get_shaqi_detail(name):
    """获取特定煞气详情"""
    _load()
    for k, v in _FENGSHUI.get("煞气", {}).items():
        if name in k:
            return {"name": k, **v}
    return None


def get_yiji():
    """获取常见风水宜忌"""
    _load()
    return _FENGSHUI.get("常见风水宜忌", {})


def get_jiuxing():
    """获取九星信息"""
    _load()
    return _FENGSHUI.get("玄空飞星", {}).get("九星", {})


def search(query):
    """模糊搜索风水知识库"""
    _load()
    results = []

    def _search_dict(d, path=""):
        for k, v in d.items():
            current_path = f"{path} > {k}" if path else k
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

    _search_dict(_FENGSHUI)
    return results
