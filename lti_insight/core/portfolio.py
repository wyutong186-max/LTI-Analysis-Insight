# -*- coding: utf-8 -*-
"""
自包含单文件 HTML 作品集页（面试官可看）。
读取 canonical records，生成内联 SVG 图表，零外部依赖，离线可用。
怡安红白配色，仅展示产品与数据，不含任何内部/技术自述。
"""
import os
import datetime
from lti_insight.config.loader import path_of

# 怡安红白配色
PALETTE = ["#E31837", "#EF6A7B", "#B8132E", "#7A7F8A", "#1F3A5F", "#C9A227"]


def _donut(segments):
    """segments: list of (label, value, color). 返回 SVG 字符串。"""
    total = sum(v for _, v, _ in segments) or 1
    cx, cy, r, sw = 120, 120, 90, 36
    circ = 2 * 3.14159265 * r
    out = [f'<svg viewBox="0 0 240 240" width="240" height="240" role="img" aria-label="工具分布">']
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#EDF1F5" stroke-width="{sw}"/>')
    offset = 0
    for label, val, color in segments:
        if val <= 0:
            continue
        frac = val / total
        len_ = frac * circ
        out.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" '
            f'stroke-width="{sw}" stroke-dasharray="{len_:.2f} {circ - len_:.2f}" '
            f'stroke-dashoffset="{-offset:.2f}" transform="rotate(-90 {cx} {cy})"/>')
        offset += len_
    out.append(f'<text x="{cx}" y="{cy-4}" text-anchor="middle" font-size="20" font-weight="700" fill="#1A1A2E">{total}</text>')
    out.append(f'<text x="{cx}" y="{cy+16}" text-anchor="middle" font-size="11" fill="#6B7280">家样本</text>')
    out.append('</svg>')
    return "\n".join(out)


def _bars(rows, maxv=1.0, color="#EF6A7B", pct=True):
    """rows: list of (label, value). 水平条形图。"""
    out = ['<svg viewBox="0 0 520 0" width="100%" style="max-width:520px"></svg>']
    h = 30 * len(rows) + 10
    out = [f'<svg viewBox="0 0 520 {h}" width="100%" style="max-width:520px" role="img">']
    for i, (label, val) in enumerate(rows):
        y = 10 + i * 30
        w = max(2, (val / maxv) * 360)
        out.append(f'<text x="0" y="{y+14}" font-size="12" fill="#374151">{label}</text>')
        out.append(f'<rect x="120" y="{y}" width="{w:.1f}" height="18" rx="3" fill="{color}"/>')
        txt = f"{val*100:.1f}%" if pct else f"{val:.0f}"
        out.append(f'<text x="{126+w:.1f}" y="{y+14}" font-size="11" fill="#374151">{txt}</text>')
    out.append('</svg>')
    return "\n".join(out)


def build_portfolio_html(records):
    """把 records 渲染为自包含单文件 HTML 字符串（不落盘，供页面内预览复用）。"""
    recs = records
    n = len(recs)
    rs2 = [r for r in recs if "第二类" in (r.get("tool_type") or "")]
    rs1 = [r for r in recs if "第一类" in (r.get("tool_type") or "")]
    combo = [r for r in recs if r.get("is_combo")]
    disc_rows = [(r["name"], r["discount_rate"]) for r in recs if r.get("discount_rate") is not None]
    max_disc = max([d for _, d in disc_rows] + [1.0])
    exec_rows = [(r["name"], r.get("exec_share_pct") or 0) for r in recs]
    max_exec = max([e for _, e in exec_rows] + [0.01])

    seg = []
    if rs2:
        seg.append(("第二类RS", len(rs2), PALETTE[0]))
    if rs1:
        seg.append(("第一类RS", len(rs1), PALETTE[2]))
    if combo:
        seg.append(("组合", len(combo), PALETTE[3]))

    rows_html = ""
    for r in recs:
        disc = f"{r['discount_rate']*100:.0f}%" if r.get("discount_rate") is not None else "组合"
        rows_html += (
            f"<tr><td>{r.get('name')}</td><td>{r.get('code')}</td><td>{r.get('board')}</td>"
            f"<td>{r.get('tool_type')}</td><td>{r.get('total_shares_wan'):.1f}</td>"
            f"<td>{disc}</td><td>{r.get('perf_metric_type')}</td>"
            f"<td>{r.get('n_recipients')}</td></tr>")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>A股 LTI 洞察 · 项目作品集</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;
color:#1A1A2E;background:#F7F9FC;line-height:1.6}}
.wrap{{max-width:960px;margin:0 auto;padding:32px 20px 64px}}
h1{{color:#1A1A2E;margin:0 0 4px}}
.sub{{color:#6B7280;margin:0 0 24px}}
.card{{background:#fff;border:1px solid #E5E9F0;border-radius:12px;padding:20px 22px;margin:16px 0;
box-shadow:0 1px 3px rgba(16,24,40,.04)}}
.grid2{{display:flex;gap:20px;flex-wrap:wrap;align-items:center}}
.grid2>div{{flex:1;min-width:260px}}
h2{{font-size:16px;color:#1A1A2E;border-left:4px solid #E31837;padding-left:10px;margin:0 0 12px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th,td{{border:1px solid #E5E9F0;padding:6px 8px;text-align:left}}
th{{background:#FBEAED;color:#B8132E}}
.foot{{color:#9CA3AF;font-size:12px;text-align:center;margin-top:28px}}
</style></head>
<body><div class="wrap">
<h1>A股长期激励（LTI）洞察</h1>
<p class="sub">从巨潮公告采集 A股股权激励草案，结构化抽取关键字段，按业务模板沉淀为活数据库，并按时段输出热点洞察报告。</p>

<div class="card">
<h2>产品流程</h2>
<svg viewBox="0 0 900 90" width="100%" style="max-width:900px" role="img" aria-label="pipeline">
<defs><marker id="a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
<path d="M0,0 L6,3 L0,6 Z" fill="#E31837"/></marker></defs>
{''.join(f'<rect x="{i*150}" y="30" width="130" height="34" rx="8" fill="{PALETTE[i%len(PALETTE)]}"/>'
         f'<text x="{i*150+65}" y="52" text-anchor="middle" fill="#fff" font-size="13">{s}</text>'
         f'<line x1="{i*150+130}" y1="47" x2="{i*150+150}" y2="47" stroke="#E31837" stroke-width="2" marker-end="url(#a)"/>'
         for i, s in enumerate(["采集公告","解析原文","抽取字段","建模入库","洞察分析","报告输出"]))}
</svg>
</div>

<div class="grid2 card">
  <div><h2>激励工具分布（{n} 家）</h2>{_donut(seg)}</div>
  <div>
    <h2>折扣率（授予价/市价）</h2>
    {_bars(disc_rows, maxv=max_disc, color=PALETTE[1])}
    <h2>高管授予占比</h2>
    {_bars(exec_rows, maxv=max_exec, color=PALETTE[4])}
  </div>
</div>

<div class="card">
<h2>样本明细（{n} 家 · {datetime.date.today().isoformat()}）</h2>
<table><thead><tr><th>公司</th><th>代码</th><th>板块</th><th>工具</th>
<th>激励总数(万)</th><th>折扣率</th><th>业绩考核</th><th>人数</th></tr></thead>
<tbody>{rows_html}</tbody></table>
</div>

<div class="foot">本页由 LTI-Insight 自动生成 · 自包含单文件 · 可直接离线打开或部署分享</div>
</div></body></html>"""
    return html


def generate_portfolio(records, out_path=None):
    """生成自包含单文件 HTML 并落盘，返回文件路径。"""
    out_path = out_path or path_of("portfolio_html")
    html = build_portfolio_html(records)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path
