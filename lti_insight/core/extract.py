# -*- coding: utf-8 -*-
"""
抽取步骤：把"草案原文文本"变成 canonical record。
当前没有可靠的自动抽取器 —— 这一步由你 / LLM 读原文完成（与现行工作流一致）。
本模块提供：① 批量导入已抽好的 canonical JSON；② UI 表单用的空模板。
"""
import json
import os
from lti_insight.config.loader import path_of


# canonical record 的字段骨架（与 fill_excel / report 对齐）
FIELDS = [
    "code", "name", "board", "industry", "announce_date", "aid", "plan_name",
    "tool_type", "is_combo", "combo_breakdown", "total_shares_wan", "total_pct",
    "first_grant_wan", "reserved_wan", "has_reserved", "grant_price", "pricing_basis",
    "market_ref_price", "discount_rate", "vesting_schedule", "vesting_labels",
    "validity_months", "perf_metric_type", "perf_relative", "perf_base", "perf_targets",
    "n_recipients", "recipients_incl_exec", "exec_share_pct", "employee_coverage_pct",
    "note", "executives",
]


def empty_record():
    """返回一个空 record 骨架，供 UI 表单预填。"""
    return {k: ([] if k in ("vesting_schedule", "vesting_labels", "combo_breakdown", "executives") else None)
            for k in FIELDS}


def import_records(json_path):
    """从 JSON 文件导入 canonical records（支持 {records:[...]} 或 [...]）。返回 list[dict]。"""
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        recs = data.get("records") or []
    else:
        recs = data
    # 仅保留已知字段，防止脏数据破坏落库
    clean = []
    for r in recs:
        clean.append({k: r.get(k) for k in FIELDS})
    return clean


def import_text(uploaded_text):
    """从粘贴的 JSON 文本导入。"""
    data = json.loads(uploaded_text)
    if isinstance(data, dict):
        recs = data.get("records") or []
    else:
        recs = data
    return [{k: r.get(k) for k in FIELDS} for r in recs]
