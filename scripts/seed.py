# -*- coding: utf-8 -*-
"""把试点 5 家的 records_5.json 灌入项目 store，并补上高管明细(executives)。
高管明细与已校验的 build_template_xlsx.py 中 EXEC 字典保持一致，确保回归输出逐字段一致。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lti_insight.config.loader import path_of

# 高管明细：(姓名, 职位, 授予量万)
EXEC = {
    "603883": [("万鑫", "副总裁", 590.35), ("王忠新", "副总裁", 52.71), ("冯诗倪", "副总裁、董事会秘书", 25.30),
               ("陈立山", "副总裁、财务负责人", 12.65), ("林欢", "副总裁", 5.90), ("党娴", "副总裁", 5.90),
               ("苏世用", "副总裁", 5.06), ("张文帅", "副总裁", 5.06), ("谭坚", "职工代表董事", 3.37)],
    "300498": [("黎少松", "董事、总裁", 360), ("梁志雄", "副董事长", 80), ("严居然", "董事", 80),
               ("秦开田", "职工代表董事、副总裁", 110), ("林建兴", "副总裁、财务总监", 90), ("张祥斌", "副总裁、技术总监", 100),
               ("蒋荣金", "副总裁、董事会秘书", 110), ("范卫朝", "副总裁", 110), ("孙建宽", "副总裁", 110)],
    "300347": [("闻增玉", "执行董事、总经理", 20.79), ("吴灏", "职工董事、联席总裁", 15.99),
               ("彭沂非", "首席运营官", 12.30), ("杨成成", "财务负责人", 9.46), ("李晓日", "董事会秘书", 1.95)],
    "688322": [("张丁军", "职工代表董事", 8.00), ("靳尚", "董事会秘书", 2.00)],
    "688169": [],
}


def main():
    proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pilot_path = os.path.join(proj_root, "..", "output", "pilot_5", "records_5.json")
    pilot_path = os.path.abspath(pilot_path)
    if not os.path.exists(pilot_path):
        raise SystemExit(f"找不到试点源文件: {pilot_path}")
    data = json.load(open(pilot_path, encoding="utf-8"))
    for r in data["records"]:
        r["executives"] = [{"name": n, "title": t, "qty_wan": q} for n, t, q in EXEC.get(r["code"], [])]
        r.setdefault("company_attr", "民营企业")
    out = path_of("records_json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(data, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"已灌入 {len(data['records'])} 家 -> {out}")


if __name__ == "__main__":
    main()
