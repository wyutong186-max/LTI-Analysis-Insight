# -*- coding: utf-8 -*-
"""
托管入口（Streamlit Community Cloud / 任意云平台）：
    streamlit run app.py

背景：Streamlit 只会把「入口脚本所在目录」加入 sys.path。
若直接把 lti_insight/ui/app.py 作为入口，sys.path 里只有 lti_insight/ui/，
而 lti_insight 包在其父目录（仓库根），会报
    ModuleNotFoundError: No module named 'lti_insight'
因此用本文件作入口：先把仓库根加入 sys.path，再执行真正的 UI 模块。
"""
import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# 导入即执行 UI（lti_insight/ui/app.py 顶层完成全部渲染）
import lti_insight.ui.app  # noqa: E402,F401
