# -*- coding: utf-8 -*-
"""
从巨潮(cninfo)拉取 A股 LTI 草案公告清单并下载原文 PDF（手动触发，无定时调度）。
接口细节见 ~/.workbuddy-ai/skills/ashare-lti-extractor/references/cninfo_api.md。
"""
import os
import re
import sys
import time
import random
import requests
from lti_insight.config.loader import load_settings

QUERY_URL = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
STATIC_URL = "http://static.cninfo.com.cn/"

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
    "Referer": "http://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Accept": "*/*",
    "X-Requested-With": "XMLHttpRequest",
}

DRAFT_RE = re.compile(r"(激励计划|员工持股计划).{0,20}(草案|预案)")
NOISE_RE = re.compile(r"(法律意见|独立财务顾问|核查意见|合规|自查|内幕信息|知情人|"
                      r"董事会|监事会|股东大会|决议|激励对象名单|"
                      r"回购注销|作废|调整|进展|实施结果|授予登记|提示性|更正|补充)")


def clean_title(t):
    return re.sub(r"\s+", " ", re.sub(r"</?em>", "", t or "")).strip()


def ts_to_date(ms):
    try:
        return time.strftime("%Y-%m-%d", time.localtime(int(ms) / 1000))
    except Exception:
        return ""


def sanitize(s):
    return re.sub(r'[\\/:*?"<>|\s]+', "_", str(s or "")).strip("_")


def doc_type_of(title):
    if "修订" in title:
        return "修订案"
    if "摘要" in title:
        return "草案摘要"
    if re.search(r"(实施|授予登记|首次授予)", title):
        return "实施公告"
    return "草案"


PLAN_CORE_RE = re.compile(r"([^，。；、\s]*?(激励计划|员工持股计划))")


def core_key(item):
    core = item["title"].replace(item["sec_name"], "")
    core = re.sub(r"^.*?(股份有限公司|有限公司|公司)", "", core)
    core = re.sub(r"(摘要|公告|之|的|关于)", "", core)
    m = PLAN_CORE_RE.search(core)
    core = m.group(1) if m else core
    core = re.sub(r"20\d{2}年?", "", core)
    core = re.sub(r"[（(]?(草案|预案)[)）]?", "", core)
    core = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9]", "", core)
    return (item["sec_code"], item["date"], core)


def query_once(session, keyword, se_date, page_num, page_size=30, retries=3):
    data = {
        "pageNum": str(page_num), "pageSize": str(page_size), "column": "szse",
        "tabName": "fulltext", "seDate": se_date, "searchkey": keyword, "isHLtitle": "true",
    }
    for i in range(retries):
        try:
            r = session.post(QUERY_URL, headers=HEADERS, data=data, timeout=25)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.5 * (i + 1) + random.random())
    raise RuntimeError(f"查询失败 [{keyword}] 第{page_num}页: {last}")


def collect(session, keywords, se_date, max_pages, sleep):
    raw = {}
    for kw in keywords:
        page, pages = 1, 1
        while page <= max_pages and page <= pages:
            j = query_once(session, kw, se_date, page)
            pages = int(j.get("totalpages") or 1)
            for a in (j.get("announcements") or []):
                raw[str(a.get("announcementId"))] = a
            if not (j.get("announcements") or []):
                break
            print(f"    [{kw}] 第{page}/{pages}页 累计去重后 {len(raw)}", file=sys.stderr)
            page += 1
            time.sleep(sleep + random.random() * 0.4)
    return raw


def download(session, item, docs_dir, retries=2):
    url = item["source_url"]
    if not url or not item.get("announcement_id"):
        return ""
    fname = sanitize(f"{item['date']}_{item['sec_code']}_{item['sec_name']}_{item['announcement_id']}") + ".pdf"
    path = os.path.join(docs_dir, fname)
    if os.path.exists(path) and os.path.getsize(path) > 1024:
        return path
    for i in range(retries):
        try:
            r = session.get(url, headers=HEADERS, timeout=60, stream=True)
            r.raise_for_status()
            with open(path, "wb") as fh:
                for chunk in r.iter_content(8192):
                    if chunk:
                        fh.write(chunk)
            return path
        except Exception:  # noqa: BLE001
            time.sleep(1.5 * (i + 1))
    return ""


def fetch_drafts(from_d, to_d, keywords=None, out_docs_dir=None, no_download=False):
    """拉取 from_d~to_d 区间的 LTI 草案清单（并集去重）。
    返回 list[dict]: sec_code, sec_name, title, date, doc_type, announcement_id, source_url, local_path。
    """
    cfg = load_settings()
    keywords = keywords or cfg["cninfo"]["keywords"]
    out_docs_dir = out_docs_dir or os.path.join(cfg["paths"]["staging_dir"])
    os.makedirs(out_docs_dir, exist_ok=True)
    se_date = f"{from_d}~{to_d}"
    print(f"[1/4] 查询区间 {se_date}，关键词：{keywords}", file=sys.stderr)
    with requests.Session() as s:
        raw = collect(s, keywords, se_date, cfg["cninfo"]["max_pages"], cfg["cninfo"]["sleep"])
        print(f"[2/4] 原始命中 {len(raw)} 条，开始标题过滤", file=sys.stderr)
        items = []
        for aid, a in raw.items():
            title = clean_title(a.get("announcementTitle"))
            if not DRAFT_RE.search(title) or NOISE_RE.search(title):
                continue
            items.append({
                "sec_code": a.get("secCode") or "",
                "sec_name": a.get("secName") or "",
                "title": title,
                "date": ts_to_date(a.get("announcementTime")),
                "doc_type": doc_type_of(title),
                "announcement_id": aid,
                "source_url": STATIC_URL + (a.get("adjunctUrl") or ""),
                "local_path": "",
            })
        groups = {}
        for it in items:
            groups.setdefault(core_key(it), []).append(it)
        picked = []
        for group in groups.values():
            full = [g for g in group if "摘要" not in g["title"]]
            picked.extend(full if full else group)
        picked.sort(key=lambda x: (x["date"], x["sec_code"]))
        print(f"[3/4] 过滤去重后 {len(picked)} 条", file=sys.stderr)
        if not no_download:
            print(f"[4/4] 下载原文到 {out_docs_dir}", file=sys.stderr)
            for i, it in enumerate(picked, 1):
                it["local_path"] = download(s, it, out_docs_dir)
                print(f"    {i}/{len(picked)} {it['sec_code']} {it['sec_name']} "
                      f"{'OK' if it['local_path'] else 'FAIL'}", file=sys.stderr)
        else:
            print("[4/4] 跳过下载（no_download）", file=sys.stderr)
    return picked
