# -*- coding: utf-8 -*-
"""
LTI-Insight 无头入口（便于每周/月底脚本化）。
  python -m lti_insight.cli update --import records.json
  python -m lti_insight.cli update --from 2026-08-01 --to 2026-08-31
  python -m lti_insight.cli report --from 2026-08-01 --to 2026-08-31 --out report.md
  python -m lti_insight.cli sync
  python -m lti_insight.cli rebuild
"""
import argparse
import os
import sys

from lti_insight.core import store, fill_excel, report, fetch, extract, sync
from lti_insight.config.loader import path_of


def _save_and_rebuild(data):
    store.save(data)
    n = fill_excel.rebuild()
    return n


def cmd_update(args):
    data = store.load()
    if args.import_path:
        recs = extract.import_records(args.import_path)
        added = store.add_many(data, recs)
        n = _save_and_rebuild(data)
        print(f"更新反馈：本次新增 {added} 家，主表现在共 {n[0]} 家。")
        return
    if args.frm and args.to:
        items = fetch.fetch_drafts(args.frm, args.to,
                                  keywords=[k.strip() for k in args.keywords.split(",") if k.strip()] if args.keywords else None,
                                  no_download=args.no_download)
        # 抓取仅产出清单 + 原文；字段抽取仍由人工/LLM 完成（见项目 README）
        manifest = os.path.join(path_of("staging_dir"), "manifest.json")
        os.makedirs(os.path.dirname(manifest), exist_ok=True)
        import json
        with open(manifest, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        print(f"抓取完成：命中 {len(items)} 份草案清单，已存 {manifest}。")
        print("下一步：抽取字段为 canonical JSON 后，运行 `update --import <json>` 落库。")
        return
    print("请指定 --import <json> 或 --from/--to 日期区间。")


def cmd_report(args):
    data = store.load()
    recs = store.filter_by_date(data, args.frm or None, args.to or None)
    if not recs:
        print("该时间范围内无数据。")
        return
    out = report.generate_report(recs, period_label=f"{args.frm or ''}~{args.to or ''}",
                                out_path=args.out)
    print(f"报告已生成：{out}（{len(recs)} 家）")


def cmd_sync(args):
    data = store.load()
    res = sync.sync_to_cumulative(data["records"], target_path=args.target)
    if res.get("ok"):
        print(f"同步完成：{res['added']}（已备份 {res.get('backup')}）")
        if res.get("skipped_sheets"):
            print("跳过：" + "；".join(res["skipped_sheets"]))
    else:
        print("未同步：" + res.get("msg"))


def cmd_rebuild(args):
    n = fill_excel.rebuild()
    print(f"已重建按模板工作簿：方案 {n[0]} 行 / 高管 {n[1]} 行 / 业绩考核 {n[2]} 行。")


def main():
    ap = argparse.ArgumentParser(description="LTI-Insight：A股 LTI 草案追踪与洞察")
    sub = ap.add_subparsers(dest="cmd")

    u = sub.add_parser("update", help="更新：导入已抽取JSON，或抓取cninfo清单")
    u.add_argument("--import", dest="import_path", help="canonical JSON 文件路径")
    u.add_argument("--from", dest="frm", help="起始日期 YYYY-MM-DD")
    u.add_argument("--to", dest="to", help="结束日期 YYYY-MM-DD")
    u.add_argument("--keywords", default="", help="关键词逗号分隔（抓取时）")
    u.add_argument("--no-download", action="store_true", help="抓取时仅出清单不下原文")

    r = sub.add_parser("report", help="生成时间范围热点报告")
    r.add_argument("--from", dest="frm", default="")
    r.add_argument("--to", dest="to", default="")
    r.add_argument("--out", default=None, help="输出 Markdown 路径")

    s = sub.add_parser("sync", help="同步到桌面 6 表累积库（可选）")
    s.add_argument("--target", default=None, help="累积库 xlsx 路径（覆盖配置）")

    sub.add_parser("rebuild", help="按当前 store 重建按模板 Excel")

    args = ap.parse_args()
    if args.cmd == "update":
        cmd_update(args)
    elif args.cmd == "report":
        cmd_report(args)
    elif args.cmd == "sync":
        cmd_sync(args)
    elif args.cmd == "rebuild":
        cmd_rebuild(args)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
