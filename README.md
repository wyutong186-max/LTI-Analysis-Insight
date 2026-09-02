# LTI-Insight

把 **A 股长期激励（LTI）股权激励草案** 的「采集 → 解析 → 抽取 → 按模板落 Excel → 热点报告」整合成一个可反复跑的工具。

- **形态**：Streamlit 网页应用（主界面）+ CLI（便于每周/月底无头跑）
- **数据入口**：cninfo 自动抓取（手动触发）**与** 手动丢 PDF/JSON 兜底
- **数据库**：工具维护自己的**按模板工作簿**（单一事实源）；可选一键同步到桌面 6 表累积库

---

## 你的工作流（项目契约）

| 触发 | 行为 |
|---|---|
| **更新请求** | 新草案 → 按公告ID(aid) 去重 → 追加进 Excel（方案/高管/业绩考核三表，严格对齐 `示例.xlsx` 157/39/159 列）→ 反馈「新增 N / 共 M」。每周增量。 |
| **总结请求** | 指定时间范围 → 过滤 → 生成热点研究报告（每统计标注来源：公司/日期/公告ID）。月底选范围出月报。 |

**硬性约定**：Excel 必须按 `示例.xlsx` 模板结构（不能用扁平表）；占比/折扣率小数存储 + 百分数格式；Excel 是唯一事实源，报告只是视图；不做自动定时调度。

---

## 安装

```bash
cd lti-insight
pip install -r requirements.txt
```

## 运行

### 网页界面（主用）
```bash
# 注意：必须设 PYTHONPATH 指向项目根目录（或者在项目根目录下运行）
# 否则 Streamlit 找不到 lti_insight 包，会报 ModuleNotFoundError
cd lti-insight
PYTHONPATH=. streamlit run lti_insight/ui/app.py
```
默认端口 `http://localhost:8501`。要换端口：`--server.port 8502`。

Tabs：概览（含单页洞察概览）/ 更新 / 数据库 / 报告 / 同步。

### 部署成公开链接（两种方式）

**A. Streamlit Community Cloud（跑完整应用，交互可用）**
1. 把本仓库推到 GitHub；
2. 打开 <https://share.streamlit.io> → New app → 选仓库、分支 `main`、**Main file path 填 `app.py`**（根目录入口 shim，负责把仓库根加入 `sys.path`）；
3. Deploy，得到 `https://<your-app>.streamlit.app`。

**B. 静态单页（零依赖，秒开，适合直接发给别人）**
```bash
PYTHONPATH=. python -c "
import json; from lti_insight.core import portfolio
recs = json.load(open('data/records.json', encoding='utf-8'))
open('site/index.html','w',encoding='utf-8').write(portfolio.build_portfolio_html(recs))
"
```
把 `site/` 目录丢到任意静态托管（GitHub Pages / Cloudflare Pages / 对象存储）即可。

### 命令行（每周 / 月底）
```bash
# 抓取某月草案清单 + 原文到 staging
python -m lti_insight.cli update --from 2026-08-01 --to 2026-08-31

# 把已抽取的 canonical JSON 导入并落库（aid 去重）
python -m lti_insight.cli update --import records.json

# 按时间范围生成热点报告
python -m lti_insight.cli report --from 2026-08-01 --to 2026-08-31 --out report.md

# 重建按模板 Excel
python -m lti_insight.cli rebuild

# 同步到桌面 6 表累积库（可选，需先配置路径）
python -m lti_insight.cli sync
```

---

## 关于「抽取」这一步（重要）

当前**没有可靠的自动抽取器** —— 字段抽取由**你 / LLM 读原文**完成（与现行工作流一致）。
工具的「更新」流水线是：

```
抓取/丢文件 → 文本 staging → 抽取(你/LLM 产出 canonical JSON 或 UI 表单) → 提交 store → 落 Excel → 报告
```

即工具负责**采集→存储→落库→报告→同步**全链路编排，**抽取语义**仍由你/LLM 提供。全自研自动抽取不在 v1 范围。

---

## 同步到累积库（可选）

`sync` 模块把 store 中的 records 写入桌面 6 表累积库（1-方案/3-高管/4-业绩考核 按列名解析写入，其余表需单独映射故跳过）。
- 在「配置」Tab 或 `lti_insight/config/settings.yaml` 设置 `paths.cumulative_db` 真实路径。
- 写入前自动备份（`.bak`），按公告ID+公司代码+预案公告日去重，小批追加。
- 文件不在 Desktop 时直接提示，不做任何改动（个人文件高风险保护）。

---

## 目录结构

```
lti-insight/
  lti_insight/
    config/        settings.yaml（路径/参数）、loader.py
    core/          store(事实源) / fill_excel(按模板落库) / report(热点报告)
                   fetch(cninfo) / parse(PDF文本) / extract(导入/表单) / portfolio(作品集) / sync / verify(回归)
    ui/            app.py（Streamlit）
    cli.py         无头入口
  data/            records.json(事实源) / output(LTI数据库_按模板.xlsx) / reports / staging / portfolio.html
  scripts/seed.py  把试点 5 家灌入 store
```

## 校验

`python -c "from lti_insight.core import fill_excel, verify; ..."` 用 `verify.compare_workbooks` 对新旧工作簿做逐字段回归比对，确保重构后输出与已校验版本一致。
