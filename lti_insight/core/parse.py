# -*- coding: utf-8 -*-
"""PDF → 文本抽取（pdfplumber），落到 staging 目录。"""
import os
import pdfplumber
from lti_insight.config.loader import path_of


def pdf_to_text(pdf_path, max_pages=25):
    parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            if i >= max_pages:
                break
            t = page.extract_text() or ""
            if t:
                parts.append(t)
    return "\n".join(parts)


def parse_to_staging(pdf_path):
    """抽取 PDF 文本，保存为 <staging>/<aid_or_name>.txt，返回文本路径。"""
    staging = path_of("staging_dir")
    os.makedirs(staging, exist_ok=True)
    base = os.path.splitext(os.path.basename(pdf_path))[0]
    txt_path = os.path.join(staging, base + ".txt")
    text = pdf_to_text(pdf_path)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)
    return txt_path, text


def parse_all(staging_dir=None):
    """批量解析 staging 下的 PDF。返回 [(pdf, txt, text), ...]。"""
    staging_dir = staging_dir or path_of("staging_dir")
    out = []
    for fn in os.listdir(staging_dir):
        if fn.lower().endswith(".pdf"):
            p = os.path.join(staging_dir, fn)
            try:
                txt, text = parse_to_staging(p)
                out.append((p, txt, text))
            except Exception as e:  # noqa: BLE001
                out.append((p, None, f"解析失败: {e}"))
    return out
