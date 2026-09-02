# -*- coding: utf-8 -*-
"""
时间范围热点研究报告生成器。
输入：已按时间范围过滤的 records 列表。
输出：Markdown 报告，所有统计标注来源（公司/日期/公告ID）。
"""
import os
import datetime
from lti_insight.config.loader import path_of


def _src(r):
    return f"{r.get('name')}（{r.get('code')}，{r.get('announce_date')}，公告ID {r.get('aid')}）"


def _pct(x):
    return "—" if x is None else f"{x * 100:.2f}%"


def _vest_short(r):
    vs = r.get("vesting_schedule") or []
    return "/".join(f"{int(x * 100)}%" for x in vs[:3])


def generate_report(records, out_path=None, period_label="所选区间"):
    out_path = out_path or os.path.join(
        path_of("reports_dir"), f"LTI热点报告_{period_label}.md")
    recs = records
    n = len(recs)
    if n == 0:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"# A股长期激励（LTI）热点研究报告\n\n**期间**：{period_label}\n\n无符合条件的数据。\n")
        return out_path

    boards = sorted(set(r.get("board") for r in recs))
    combo = [r for r in recs if r.get("is_combo")]
    single = [r for r in recs if not r.get("is_combo")]
    rs2 = [r for r in single if "第二类" in (r.get("tool_type") or "")]
    rs1 = [r for r in single if "第一类" in (r.get("tool_type") or "")]
    total_shares = sum((r.get("total_shares_wan") or 0) for r in recs)
    disc_vals = [(r, r.get("discount_rate")) for r in recs if r.get("discount_rate") is not None]
    floor = [r for r, d in disc_vals if abs(d - 0.5) < 0.01]
    above = [r for r, d in disc_vals if d and d > 0.55]
    perf_types = sorted(set(r.get("perf_metric_type") for r in recs))
    exec_recs = [r for r in recs if r.get("recipients_incl_exec")]
    max_exec = max(exec_recs, key=lambda r: (r.get("exec_share_pct") or 0)) if exec_recs else None
    lockup = [r for r in recs if any(k in (r.get("note") or "") for k in ("禁售", "限售"))]

    L = []
    L.append("# A股长期激励（LTI）热点研究报告")
    L.append("")
    L.append(f"**报告期**：{period_label}（样本 {n} 家）")
    L.append(f"**生成日期**：{datetime.date.today().isoformat()}")
    L.append("**数据来源**：巨潮资讯（cninfo）上市公司股权激励/员工持股计划**草案**全文，经人工复核结构化抽取")
    L.append("**工作机制**：每周增量更新草案库 -> 按选定时间范围自动生成洞察报告")
    L.append("")
    L.append("> 说明：本报告所有统计均标注来源（公司/公告日期/公告ID）。占比字段以小数存储、百分比展示；"
             "折扣率 = 授予价（或行权价）÷ 推算市价（全价）。")
    L.append("")

    # 执行摘要
    L.append("## 一、执行摘要")
    L.append("")
    L.append(f"本报告覆盖 **{n} 家** 公司、横跨 **{len(boards)} 个板块**（{'、'.join(boards)}），"
             f"合计拟授予权益 **{total_shares:.2f} 万股/万份**。"
             f"工具以限制性股票为主（第二类 {len(rs2)} 家、第一类 {len(rs1)} 家），"
             f"组合工具（期权+第二类RS）{len(combo)} 家。")
    L.append("")
    L.append("**核心发现：**")
    if above:
        L.append(f"1. **折扣率分化**：{len(floor)} 家贴 50% 监管底线；"
                 f"**{'、'.join(r['name'] for r in above)}** 主动高于底线"
                 f"（折扣率 {'、'.join(_pct(r['discount_rate']) for r in above)}），偏股东友好。")
    else:
        L.append(f"1. **折扣率高度集中底线**：{len(floor)} 家均贴 50% 监管底线定价。")
    if combo:
        L.append(f"2. **组合工具创新**：{'、'.join(r['name'] for r in combo)} 采用「期权+第二类RS」组合"
                 f"（来源：{'; '.join(_src(r) for r in combo)}）。")
    L.append(f"3. **业绩考核多元化**：覆盖 {len(perf_types)} 类指标 —— {'、'.join(perf_types)}。")
    if max_exec:
        L.append(f"4. **高管集中度**：最高为 {max_exec['name']}（高管授予占比 {_pct(max_exec['exec_share_pct'])}，"
                 f"来源：{_src(max_exec)}）；另有 {sum(1 for r in recs if not r.get('recipients_incl_exec'))} 家为纯骨干方案。")
    if lockup:
        L.append(f"5. **额外限售成趋势**：{'、'.join(r['name'] for r in lockup)} 设额外禁售/限售期"
                 f"（来源：{'; '.join(_src(r) for r in lockup)}）。")
    L.append("")

    # 数据与方法
    L.append("## 二、数据与方法")
    L.append("")
    L.append("- **采集入口**：巨潮 hisAnnouncement/query，以关键词拉取全量公告，按 seDate 时间窗过滤草案。")
    L.append("- **识别规则**：标题命中 (激励计划|员工持股计划).{0,20}(草案|预案) 且排除摘要/名单/法律意见/核查意见等噪声。")
    L.append("- **解析**：草案 PDF 全文经 pdfplumber 抽取文本，逐家人工复核关键字段并固化为结构化记录。")
    L.append("- **下游机制**：每周增量抽取新发草案追加至数据库；按所选时间范围自动生成本报告。")
    L.append("")

    # 市场概览
    L.append("## 三、市场概览")
    L.append("")
    L.append("| 公司 | 板块 | 工具 | 激励总数(万) | 占股本 | 授予价 | 折扣率 | 归属节奏 | 业绩考核 | 激励人数 |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in recs:
        disc = _pct(r.get("discount_rate")) if r.get("discount_rate") is not None else "组合"
        L.append(f"| {r.get('name')} | {r.get('board')} | {r.get('tool_type')} | {r.get('total_shares_wan'):.2f} "
                 f"| {_pct(r.get('total_pct'))} | {r.get('grant_price')} | {disc} | {_vest_short(r)} | "
                 f"{r.get('perf_metric_type')} | {r.get('n_recipients')}人"
                 f"{'（含高管）' if r.get('recipients_incl_exec') else '（纯骨干）'} |")
    L.append("")
    L.append("*数据来源：上述字段均取自各公司草案原文（公告ID 见附录）。*")
    L.append("")

    # 热点研究
    L.append("## 四、热点研究")
    L.append("")
    L.append("### 4.1 折扣率：50% 底线共识下的分化信号")
    L.append("")
    if floor:
        L.append(f"{len(floor)} 家限制性股票授予价严格贴附「前N日均价50%」底线"
                 f"（{'、'.join(r['name'] for r in floor)}）。")
    if above:
        L.append(f"**{'、'.join(r['name'] for r in above)}** 是唯一例外：折扣率 "
                 f"{'、'.join(_pct(r['discount_rate']) for r in above)}，高于 50% 底线，"
                 f"对现有股东稀释更小但员工出资门槛更高。「是否贴 50% 底线」成为观察激励倾向的窗口。"
                 f"（来源：{'; '.join(_src(r) for r in above)}）")
    if not floor and not above:
        L.append("本期样本无明确折扣率数据。")
    L.append("")

    L.append("### 4.2 工具组合创新")
    L.append("")
    if combo:
        for r in combo:
            cb = r.get("combo_breakdown") or {}
            opt = cb.get("期权万份"); optp = cb.get("期权占权益总额")
            rst = cb.get("限制性万股"); rstp = cb.get("限制性占权益总额")
            L.append(f"- **{r['name']}**：股票期权 {opt} 万份（{optp*100:.1f}%）+ 第二类限制性股票 {rst} 万股（{rstp*100:.1f}%），"
                     f"反映科创板工具灵活度优势（来源：{_src(r)}）。")
    else:
        L.append("本期无组合工具案例，全部为单一限制性股票。")
    L.append("")

    L.append("### 4.3 业绩考核范式")
    L.append("")
    for pt in perf_types:
        names = [r['name'] for r in recs if r.get('perf_metric_type') == pt]
        L.append(f"- **{pt}**：{'、'.join(names)}")
    L.append("")

    L.append("### 4.4 高管集中度")
    L.append("")
    for r in sorted(exec_recs, key=lambda x: -(x.get("exec_share_pct") or 0)):
        L.append(f"- **{r['name']}**：高管授予占比 {_pct(r.get('exec_share_pct'))}（来源：{_src(r)}）。")
    pure = [r['name'] for r in recs if not r.get('recipients_incl_exec')]
    if pure:
        L.append(f"- 纯骨干（高管零参与）：{'、'.join(pure)}。")
    L.append("")

    L.append("### 4.5 长周期与额外限售")
    L.append("")
    if lockup:
        for r in lockup:
            L.append(f"- **{r['name']}**：{r.get('note')}（来源：{_src(r)}）")
    else:
        L.append("本期样本未见额外禁售安排。")
    L.append("")

    # 工具配比
    L.append("## 五、工具配比分析")
    L.append("")
    L.append(f"- 单一第二类限制性股票：**{len(rs2)} 家**")
    L.append(f"- 单一第一类限制性股票：**{len(rs1)} 家**")
    L.append(f"- 组合（股票期权 + 第二类RS）：**{len(combo)} 家**")
    L.append("")
    board_dist = "；".join(f"{b} {sum(1 for r in recs if r.get('board') == b)}家" for b in boards)
    L.append(f"**结论**：限制性股票（尤其第二类）是当前绝对主流；股票期权仅以组合形式出现。"
             f"板块分布：{board_dist}。")
    L.append("")

    # 典型个案
    L.append("## 六、典型个案")
    L.append("")
    picks = []
    if combo:
        picks.append(combo[0])
    if max_exec:
        picks.append(max_exec)
    above_sorted = sorted(above, key=lambda r: -(r.get("discount_rate") or 0))
    if above_sorted:
        picks.append(above_sorted[0])
    picks = picks[:4]
    if not picks:
        picks = recs[:3]
    for r in picks:
        L.append(f"### {r['name']}（{r['code']}）")
        L.append(f"{_src(r)}。{r.get('note')}")
        L.append("")

    # 附录
    L.append("## 七、附录：全量 Canonical 数据")
    L.append("")
    for r in recs:
        L.append(f"### {r.get('name')}（{r.get('code')}）")
        L.append(f"- 公告日期 / ID：{r.get('announce_date')} / {r.get('aid')}")
        L.append(f"- 板块 / 行业：{r.get('board')} / {r.get('industry')}")
        L.append(f"- 计划名称：{r.get('plan_name')}")
        combo_txt = ""
        if r.get("is_combo"):
            cb = r.get("combo_breakdown") or {}
            combo_txt = f"；组合拆分：期权 {cb.get('期权万份')} 万份（{cb.get('期权占权益总额')*100:.1f}%）" \
                        f"+ 限制性 {cb.get('限制性万股')} 万股（{cb.get('限制性占权益总额')*100:.1f}%）"
        L.append(f"- 工具：{r.get('tool_type')}{combo_txt}")
        L.append(f"- 激励总数：{r.get('total_shares_wan'):.2f} 万（占股本 {_pct(r.get('total_pct'))}）；"
                 f"首次 {r.get('first_grant_wan'):.2f} / 预留 {r.get('reserved_wan'):.2f}")
        disc_txt = _pct(r.get("discount_rate")) if r.get("discount_rate") is not None else "组合(限制性50%/期权100%)"
        L.append(f"- 授予价：{r.get('grant_price')} 元；定价基准：{r.get('pricing_basis')}；折扣率：{disc_txt}")
        L.append(f"- 归属/行权节奏：{' / '.join(r.get('vesting_labels') or [])}；有效期 <={r.get('validity_months')} 个月")
        L.append(f"- 业绩考核：{r.get('perf_metric_type')}；{r.get('perf_base')}；{r.get('perf_targets')}")
        exec_txt = "是" if r.get("recipients_incl_exec") else "否"
        L.append(f"- 激励对象：{r.get('n_recipients')} 人；含高管：{exec_txt}；"
                 f"高管获授占比：{_pct(r.get('exec_share_pct'))}")
        L.append(f"- 备注：{r.get('note')}")
        L.append("")

    L.append("---")
    L.append(f"*本报告由 LTI 自动化抽取 + 人工复核流程生成，样本 {n} 家（期间 {period_label}）。*")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    return out_path
