# -*- coding: utf-8 -*-
"""
Canonical records 仓库 —— 整个系统的单一事实源。
records.json 结构：{"meta": {...}, "records": [ {...}, ... ]}
每条 record 字段沿用 records_5.json 的口径，并新增可选字段：
  - executives: [{name, title, qty_wan}, ...]  （用于「高管」表）
  - extra_lockup_months: int  （额外禁售/限售月数，用于热点识别）
去重主键：aid（公告ID）。
"""
import os
import json
from lti_insight.config.loader import path_of


def _records_path():
    return path_of("records_json")


def load(path=None):
    path = path or _records_path()
    if not os.path.exists(path):
        return {"meta": {"n_companies": 0, "source": "cninfo 草案公告（人工复核抽取）"}, "records": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(data, path=None):
    path = path or _records_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add(data, record):
    """追加一条；aid 已存在则跳过。返回 True=新增。"""
    recs = data.setdefault("records", [])
    by_aid = {r.get("aid"): r for r in recs}
    aid = record.get("aid")
    if aid and aid in by_aid:
        return False
    recs.append(record)
    data["meta"]["n_companies"] = len(recs)
    return True


def add_many(data, records):
    n = 0
    for r in records:
        if add(data, r):
            n += 1
    return n


def filter_by_date(data, from_d=None, to_d=None):
    recs = data.get("records", [])

    def in_range(r):
        d = r.get("announce_date", "")
        if from_d and (d < from_d):
            return False
        if to_d and (d > to_d):
            return False
        return True

    return [r for r in recs if in_range(r)]


def stats(data):
    recs = data.get("records", [])
    boards, tools = {}, {}
    for r in recs:
        b = r.get("board", "未知")
        t = r.get("tool_type", "未知")
        boards[b] = boards.get(b, 0) + 1
        tools[t] = tools.get(t, 0) + 1
    n_exec = sum(1 for r in recs if r.get("recipients_incl_exec"))
    return {
        "n": len(recs),
        "boards": boards,
        "tools": tools,
        "total_shares_wan": sum((r.get("total_shares_wan") or 0) for r in recs),
        "with_exec": n_exec,
    }
