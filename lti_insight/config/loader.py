# -*- coding: utf-8 -*-
"""读取 settings.yaml 并解析为绝对路径。"""
import os
import yaml
from lti_insight import BASE


def load_settings():
    p = os.path.join(os.path.dirname(__file__), "settings.yaml")
    with open(p, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    # 本机私有覆盖：settings.local.yaml（已在 .gitignore 中，不会外发）
    local = os.path.join(os.path.dirname(__file__), "settings.local.yaml")
    if os.path.exists(local):
        with open(local, encoding="utf-8") as f:
            loc = yaml.safe_load(f) or {}
        for k, v in (loc.get("paths") or {}).items():
            cfg.setdefault("paths", {})[k] = v
        for k, v in loc.items():
            if k != "paths":
                cfg[k] = v

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
