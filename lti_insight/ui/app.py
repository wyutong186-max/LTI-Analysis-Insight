# -*- coding: utf-8 -*-
"""
LTI-Insight Streamlit 界面。
Tab：公司明细 / 更新 / 数据库 / 报告 / 同步
"""
import os
import sys

# 自举 sys.path：让 `import lti_insight` 在任意启动方式下都能工作。
# Streamlit `streamlit run lti_insight/ui/app.py` 时只会把脚本所在目录
# (lti_insight/ui/) 加入 sys.path，而 lti_insight package 在它的父目录，
# 因此需要显式把项目根目录加进路径。
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import json
import datetime
import streamlit as st
import streamlit.components.v1 as components

from lti_insight.core import store, fill_excel, report, portfolio, fetch, parse, extract, sync
from lti_insight.core.demo_template import DISCLAIMER
from lti_insight.config.loader import load_settings, path_of

st.set_page_config(
    page_title="LTI-Insight · A股长期激励",
    layout="wide",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "LTI-Insight · Aon 风格红白主题",
    },
)


def _style():
    """注入 Aon 红白主题（简洁版），并渲染自定义头部。"""
    st.markdown(
        """
        <style>
        :root{
          --aon-red:#E31837;
          --aon-red-dark:#B8132E;
          --aon-red-soft:#FCE7EA;
          --ink:#1A1A2E;
          --muted:#6B7280;
          --bg:#FFFFFF;
          --bg-soft:#F7F8FA;
          --border:#ECEEF2;
        }
        /* 全局字体与留白 */
        html,body,[class*="css"]{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei","Segoe UI",sans-serif;}
        .block-container{padding-top:1.5rem;padding-bottom:2rem;}
        /* 顶部细红条 */
        .aon-bar{height:4px;background:var(--aon-red);border-radius:999px;margin-bottom:14px;}
        /* 头部（基线对齐，避免错位） */
        .aon-head{display:flex;align-items:baseline;gap:10px;margin:0 0 1.1rem 0;line-height:1.2;}
        .aon-logo{font-size:1.5rem;font-weight:800;color:var(--ink);letter-spacing:-.4px;line-height:1.2;}
        .aon-red{color:var(--aon-red);}
        .aon-title{font-size:.9rem;color:var(--muted);font-weight:500;line-height:1.2;}

        /* 标题：红竖条高度 = 1em（等于字号），垂直居中
           → 竖条上下端与字体上下端对齐，不会因行高而外溢 */
        h1,h2,h3{
          position:relative;color:var(--ink)!important;font-weight:700;
          line-height:1.2;padding-top:0!important;padding-bottom:0!important;
          margin-top:.35rem;margin-bottom:.7rem;
        }
        h1::before,h2::before,h3::before{
          content:"";position:absolute;left:0;top:50%;
          transform:translateY(-50%);height:1em;width:4px;
          border-radius:2px;background:var(--aon-red);
        }
        h1{font-size:1.4rem;padding-left:14px!important;}
        h1::before{width:5px;}
        h2{font-size:1.12rem;padding-left:12px!important;}
        h2::before{width:4px;}
        h3{font-size:.98rem;padding-left:10px!important;}
        h3::before{width:3px;}

        /* 指标卡 */
        [data-testid="stMetric"]{
          background:var(--bg-soft);border:1px solid var(--border);
          border-top:3px solid var(--aon-red);border-radius:12px;
          padding:14px 16px;box-shadow:0 1px 2px rgba(20,20,40,.04);
        }
        [data-testid="stMetricLabel"]{color:var(--muted)!important;font-size:.78rem!important;font-weight:600;line-height:1.35;}
        [data-testid="stMetricValue"]{color:var(--ink)!important;font-size:1.55rem!important;font-weight:800;line-height:1.2;}

        /* 按钮：默认红填充，次要按钮描边 */
        .stButton>button{
          background:var(--aon-red);color:#fff;border:none;border-radius:8px;
          padding:.5rem 1.1rem;font-weight:600;transition:.15s;
        }
        .stButton>button:hover{background:var(--aon-red-dark);box-shadow:0 4px 12px rgba(227,24,55,.25);}
        .stButton>button:active{transform:translateY(1px);}

        /* Tabs */
        .stTabs [data-baseweb="tab-list"]{gap:2px;border-bottom:1px solid var(--border);}
        .stTabs [data-baseweb="tab"]{border-radius:8px 8px 0 0;color:var(--muted);font-weight:600;font-size:.92rem;padding:.5rem .9rem;line-height:1.3;}
        .stTabs [data-baseweb="tab"]:hover{color:var(--aon-red);}
        .stTabs [aria-selected="true"]{color:var(--aon-red)!important;border-bottom:2px solid var(--aon-red)!important;}
        .stTabs [data-baseweb="tab-highlight"]{background-color:var(--aon-red)!important;}

        /* Expander 标题 */
        .streamlit-expanderHeader{font-weight:600;color:var(--ink);font-size:.92rem;}
        [data-testid="stExpander"]{border:1px solid var(--border);border-radius:10px;}

        /* 数据表圆角 */
        [data-testid="stDataFrame"]{border:1px solid var(--border);border-radius:12px;overflow:hidden;}

        /* caption / 分隔 */
        .stCaption{color:var(--muted)!important;font-size:.82rem;line-height:1.4;}
        hr{border:none;border-top:1px solid var(--border);}
        /* 输入控件统一圆角 */
        .stTextInput>div>div>input,.stDateInput>div>div>input,.stSelectbox>div>div,.stMultiSelect>div>div{
          border-radius:8px!important;border-color:var(--border)!important;font-size:.9rem;
        }
        /* 收起 Streamlit 默认页脚与菜单，页面更干净 */
        footer{visibility:hidden;}
        #MainMenu{visibility:hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="aon-bar"></div>
        <div class="aon-head">
          <div class="aon-logo">LTI<span class="aon-red">·</span>Insight</div>
          <div class="aon-title">A股长期激励草案 · 追踪与洞察</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


_style()


def _rebuild(data):
    n = fill_excel.rebuild()
    return n


def _feedback(added, total):
    st.success(f"更新反馈：本次新增 **{added}** 家，主表现在共 **{total}** 家（按预案公告日排序）。")


DATE_FMT = "YYYY-MM-DD"
DATE_HINT = "日期格式 YYYY-MM-DD，点击输入框即可从日历中选择（也支持手动输入）。"


def _d(s, fallback=None):
    """'YYYY-MM-DD' → datetime.date；解析失败退回 fallback 或今天。"""
    try:
        return datetime.date.fromisoformat(str(s).strip()[:10])
    except Exception:
        return fallback or datetime.date.today()


# ============================ 公司明细（首屏） ============================
def _companies_df(recs):
    """把 records 转成「公司明细」表格用的行列表（与数据库页共用）。"""
    return [{
        "代码": r["code"], "名称": r["name"], "板块": r["board"], "工具": r["tool_type"],
        "总数(万)": r["total_shares_wan"], "占股本": f"{r['total_pct']*100:.2f}%",
        "授予价": r["grant_price"],
        "折扣率": (f"{r['discount_rate']*100:.0f}%" if r.get("discount_rate") else "组合"),
        "人数": r["n_recipients"], "公告日": r["announce_date"],
    } for r in recs]


def tab_overview():
    st.header("公司明细")
    data = store.load()
    recs = data["records"]
    st.caption(DISCLAIMER)
    st.caption("数据来源：巨潮资讯网 A股 股权激励 / 员工持股计划草案公告")

    s = store.stats(data)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("样本公司", s["n"])
    c2.metric("合计激励(万股)", f"{s['total_shares_wan']:,.1f}")
    c3.metric("含高管方案", s["with_exec"])
    c4.metric("板块数", len(s["boards"]))

    st.subheader("公司明细清单")
    st.dataframe(
        _companies_df(recs),
        width="stretch",
        column_config={
            "总数(万)": st.column_config.NumberColumn("总数(万)", format="%.2f"),
            "授予价": st.column_config.NumberColumn("授予价", format="%.2f"),
            "人数": st.column_config.NumberColumn("人数", format="%d"),
        },
    )


# ============================ 更新 ============================
def tab_update():
    st.header("更新（增量落库）")
    st.caption("从巨潮自动抓取草案，或导入已抽取记录 / 上传 PDF 解析原文，增量沉淀为活数据库。")

    with st.expander("A. 从巨潮抓取草案", expanded=False):
        st.caption(DATE_HINT)
        col1, col2 = st.columns(2)
        from_d = col1.date_input("起始日期", value=_d("2026-08-01"), format=DATE_FMT, key="ufd")
        to_d = col2.date_input("结束日期", value=_d("2026-08-31"), format=DATE_FMT, key="utd")
        keywords = st.text_input("关键词(逗号分隔)", "股权激励,限制性股票,股票期权,员工持股")
        no_dl = st.checkbox("仅出清单不下原文", False)
        if st.button("运行抓取", key="fetch"):
            fd, td = from_d.strftime("%Y-%m-%d"), to_d.strftime("%Y-%m-%d")
            if fd > td:
                fd, td = td, fd
            with st.spinner("正在查询巨潮…"):
                items = fetch.fetch_drafts(fd, td,
                                          keywords=[k.strip() for k in keywords.split(",") if k.strip()],
                                          no_download=no_dl)
            st.session_state["manifest"] = items
            st.success(f"命中 {len(items)} 份草案（已去重）。可在下方上传 PDF 解析或导入已抽取记录。")
            if items:
                st.dataframe([{ "代码": i["sec_code"], "名称": i["sec_name"], "标题": i["title"],
                                "日期": i["date"], "公告ID": i["announcement_id"]} for i in items])

    with st.expander("B. 导入已抽取记录(JSON)", expanded=True):
        st.caption("导入已抽取的记录文件（JSON），追加进活数据库。")
        up = st.file_uploader("选择记录 JSON", type=["json"], key="imp")
        if up is not None:
            txt = up.getvalue().decode("utf-8")
            if st.button("导入并提交", key="imp_btn"):
                recs = extract.import_text(txt)
                data = store.load()
                added = store.add_many(data, recs)
                store.save(data)
                _rebuild(data)
                _feedback(added, len(data["records"]))

    with st.expander("C. 上传 PDF 解析为文本", expanded=False):
        up = st.file_uploader("选择草案 PDF", type=["pdf"], key="pdf")
        if up is not None:
            staging = path_of("staging_dir")
            os.makedirs(staging, exist_ok=True)
            p = os.path.join(staging, up.name)
            with open(p, "wb") as f:
                f.write(up.getvalue())
            txt_path, text = parse.parse_to_staging(p)
            st.success(f"已解析：{txt_path}")
            st.text_area("草案文本（供抽取参考）", text[:6000], height=300)

    with st.expander("D. 手动填写一条记录", expanded=False):
        st.caption("抽取完成后，在此录入关键字段。高管明细可在下方逐条添加。")
        with st.form("rec_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            code = c1.text_input("公司代码*")
            name = c2.text_input("公司名称*")
            board = c1.text_input("上市板", "科创板")
            industry = c2.text_input("行业", "")
            announce_date = c1.date_input("预案公告日*", value=_d("2026-08-01"), format=DATE_FMT, key="mfd")
            aid = c2.text_input("公告ID*")
            plan_name = st.text_input("计划名称", "2026年限制性股票激励计划")
            tool_type = st.selectbox("激励工具", ["第二类限制性股票", "第一类限制性股票",
                                                  "组合（股票期权+第二类限制性股票）", "股票期权", "员工持股计划"])
            c1, c2, c3 = st.columns(3)
            total_shares_wan = c1.number_input("激励总数(万)", 0.0, 1e7, 0.0)
            total_pct = c2.number_input("占总股本比例(%)", 0.0, 100.0, 0.0) / 100.0
            grant_price = c3.number_input("授予价", 0.0, 1e5, 0.0)
            disc = st.number_input("折扣率(%)", 0.0, 200.0, 50.0) / 100.0
            vest = st.text_input("归属节奏(分号分隔比例, 如 0.25;0.25;0.25;0.25)", "0.25;0.25;0.25;0.25")
            perf = st.text_input("业绩考核指标", "营业收入")
            n_rec = st.number_input("激励总人数", 0, 1_000_000, 0)
            note = st.text_area("备注", "")
            submit = st.form_submit_button("提交并落库")
            if submit:
                if not (code and name and announce_date and aid):
                    st.error("代码/名称/公告日期/公告ID 为必填")
                else:
                    rec = {
                        "code": code, "name": name, "board": board, "industry": industry,
                        "announce_date": announce_date.strftime("%Y-%m-%d"), "aid": aid, "plan_name": plan_name,
                        "tool_type": tool_type, "is_combo": "组合" in tool_type,
                        "total_shares_wan": total_shares_wan, "total_pct": total_pct,
                        "first_grant_wan": total_shares_wan, "reserved_wan": 0.0, "has_reserved": False,
                        "grant_price": grant_price, "discount_rate": disc,
                        "vesting_schedule": [float(x) for x in vest.split(";") if x.strip()],
                        "perf_metric_type": perf, "n_recipients": int(n_rec),
                        "recipients_incl_exec": False, "note": note, "executives": [],
                    }
                    data = store.load()
                    added = store.add(data, rec)
                    store.save(data)
                    _rebuild(data)
                    _feedback(1 if added else 0, len(data["records"]))


# ============================ 数据库 ============================
def tab_db():
    st.header("数据库（按模板活库）")
    _, is_demo = fill_excel.resolve_headers(path_of("template_xlsx"))
    if is_demo:
        st.info(DISCLAIMER)
    data = store.load()
    recs = data["records"]
    # 日期筛选：默认关闭；开启后用日历选择，默认范围取库内公告日区间
    _dates = [r.get("announce_date", "") for r in recs if r.get("announce_date")]
    dmin = min(_dates) if _dates else datetime.date.today().isoformat()
    dmax = max(_dates) if _dates else datetime.date.today().isoformat()
    st.caption(DATE_HINT)
    use_date = st.checkbox("按预案公告日筛选", value=False, key="dbuse")
    col1, col2 = st.columns(2)
    from_d = col1.date_input("起始日期", value=_d(dmin), format=DATE_FMT, disabled=not use_date, key="dbf")
    to_d = col2.date_input("结束日期", value=_d(dmax), format=DATE_FMT, disabled=not use_date, key="dbt")
    boards = sorted(set(r.get("board") for r in recs))
    tools = sorted(set(r.get("tool_type") for r in recs))
    sel_b = st.multiselect("板块筛选", boards)
    sel_t = st.multiselect("工具筛选", tools)
    filt = recs
    if use_date:
        fd, td = from_d.strftime("%Y-%m-%d"), to_d.strftime("%Y-%m-%d")
        if fd > td:
            fd, td = td, fd
        filt = [r for r in filt if fd <= r.get("announce_date", "") <= td]
    if sel_b:
        filt = [r for r in filt if r.get("board") in sel_b]
    if sel_t:
        filt = [r for r in filt if r.get("tool_type") in sel_t]
    df = _companies_df(filt)
    st.dataframe(df, width="stretch")
    if st.button("重新生成按模板 Excel", key="regen"):
        _rebuild(data)
        st.success("已刷新 LTI数据库_按模板.xlsx")
    out = path_of("output_dir")
    xlsx = os.path.join(out, "LTI数据库_按模板.xlsx")
    if os.path.exists(xlsx):
        with open(xlsx, "rb") as f:
            st.download_button("下载按模板 Excel", f.read(), file_name="LTI数据库_按模板.xlsx")


# ============================ 报告 ============================
def tab_report():
    st.header("热点研究报告（按时间范围）")
    st.caption(DATE_HINT)
    col1, col2 = st.columns(2)
    from_d = col1.date_input("起始日期", value=_d("2026-08-01"), format=DATE_FMT, key="rf")
    to_d = col2.date_input("结束日期", value=_d("2026-08-31"), format=DATE_FMT, key="rt")
    if st.button("生成报告", key="genrpt"):
        fd, td = from_d.strftime("%Y-%m-%d"), to_d.strftime("%Y-%m-%d")
        if fd > td:
            fd, td = td, fd
        data = store.load()
        recs = store.filter_by_date(data, fd, td)
        if not recs:
            st.warning("该时间范围内没有数据。")
            return
        out = report.generate_report(recs, period_label=f"{fd} ~ {td}")
        with open(out, encoding="utf-8") as f:
            md = f.read()
        st.markdown(md)
        with open(out, "rb") as f:
            st.download_button("下载报告(Markdown)", f.read(), file_name=os.path.basename(out))


# ============================ 同步 ============================
def tab_sync():
    st.header("同步到桌面 6 表累积库（可选）")
    cfg = load_settings()
    cum = st.text_input("累积库路径(留空=未配置)", cfg["paths"].get("cumulative_db", ""))
    if st.button("执行同步", key="dosync"):
        data = store.load()
        res = sync.sync_to_cumulative(data["records"], target_path=cum or None)
        if res.get("ok"):
            st.success(f"同步完成。各表新增：{res['added']}（已备份至 {res.get('backup')}）")
            if res.get("skipped_sheets"):
                st.warning("部分表跳过：" + "；".join(res["skipped_sheets"]))
        else:
            st.error(res.get("msg"))


# ============================ 配置（内部，不在演示 Tab 暴露） ============================
def tab_config():
    st.header("配置")
    cfg = load_settings()
    st.json({k: (v if not str(v).startswith("C:/") else "…") for k, v in cfg["paths"].items()})
    st.subheader("修改模板 / 累积库路径")
    tp = st.text_input("template_xlsx", cfg["paths"].get("template_xlsx", ""))
    cum = st.text_input("cumulative_db", cfg["paths"].get("cumulative_db", ""))
    if st.button("保存配置", key="savecfg"):
        settings_path = os.path.join(os.path.dirname(__file__), "..", "config", "settings.yaml")
        settings_path = os.path.abspath(settings_path)
        import yaml
        with open(settings_path, encoding="utf-8") as f:
            c = yaml.safe_load(f)
        c["paths"]["template_xlsx"] = tp
        c["paths"]["cumulative_db"] = cum
        with open(settings_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(c, f, allow_unicode=True)
        st.success("已保存（重新运行生效）。")


TABS = {
    "公司明细": tab_overview,
    "更新": tab_update,
    "数据库": tab_db,
    "报告": tab_report,
    "同步": tab_sync,
}

selection = st.tabs(list(TABS.keys()))
for tab, (name, fn) in zip(selection, TABS.items()):
    with tab:
        fn()
