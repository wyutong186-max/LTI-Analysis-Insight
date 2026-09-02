# -*- coding: utf-8 -*-
"""读取 settings.yaml 并解析为绝对路径。"""
import os
import yaml
from lti_insight import BASE


def load_settings():
    p = os.path.join(os.path.dirname(__file__), "settings.yaml")
    with open(p, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    def resolve(v):
        if not v:
            return v
        if os.path.isabs(v):
            return v
        return os.path.join(BASE, v)

    paths = cfg.get("paths", {})
    cfg["paths"] = {k: resolve(v) for k, v in paths.items()}
    return cfg


def path_of(key):
    return load_settings()["paths"].get(key, "")
