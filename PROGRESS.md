# TrendRadar - Development Progress

> Last updated: 2026-05-01 (session 4)
> Reference: `Outline.md` (implementation brief), `config.yaml` (profile + leaders)

## Current Status: Phase 1 Feature Complete + Skill 封装完成

---

## Phase 0: Design & Configuration (2026-04-30 ~ 2026-05-01)

### 0.1 Project Design (DONE)

- **Design doc**: `~/.gstack/projects/ClaudeCode/12845-unknown-design-20260430-204842.md`
  - 通过 /office-hours 完成头脑风暴和可行性验证
  - 经过 3 轮对抗性审查 (27 issues found, 23 fixed, 4 deferred)
  - 确定路线: Approach A (validation prototype) -> Approach C (agent evolution)
  - Status: APPROVED

- **Implementation brief**: `Outline.md`
  - 初版采用 per-item scoring 架构
  - **关键转折**: 用户明确指出"评分只是手段，简报才是目的"
  - 完全重写为 briefing-first 架构: scrape all data -> one LLM call -> narrative report
  - 确定 6 个简报板块 (后扩展为 ArXiv 论文独立板块)

### 0.2 Research Profile (DONE)

`config.yaml` profile section 包含:
- Identity: 东南大学 HCI 方向研究生, 职业规划面向游戏行业
- 3 个核心研究方向: HCI (XR/VR/HAI), Game Design & Dev, AI Tools
- Current focus: Meta-Interaction (LLM-driven narrative + scaffold system, CHI 2026 MAVIS)
- 17 个关键词 (HCI/游戏/AI 三类)
- 8 个游戏品味偏好, 2 个短板方向, 6 个 AI 工具追踪品类

### 0.3 Leader List (DONE — 27 leaders, 7 categories)

通过 /leader-scout 技能逐一搜索验证。详见 config.yaml。

### 0.4 Tooling (DONE)

- `/leader-scout` skill (`~/.claude/skills/leader-scout/SKILL.md`)

---

## Phase 1: Approach A — Validation Prototype (2026-05-01)

> Status: **FEATURE COMPLETE**

### 1.1 scrape.py (DONE)

三个数据源:
- [x] `scrape_github(leaders)`: starred repos + public events (30 items/leader)
- [x] `scrape_semantic_scholar(leaders)`: 近 30 天论文 (需 semantic_scholar ID)
- [x] `scrape_arxiv(profile)`: **新增** — 基于关键词搜索 ArXiv 近 7 天论文
- [x] 输出 `items.json`, 错误处理: print + skip
- [x] 支持从 `.env` 文件读取环境变量
- [x] `follow_redirects=True` 解决 ArXiv HTTP->HTTPS 重定向

**ArXiv 抓取策略**:
- 3 个宽查询 (HCI+XR+VR / Game+PCG / LLM+GenAI), 各 15 条, 去重后保留最多 30 篇
- 限定 ArXiv 分类: cs.HC, cs.AI, cs.GR, cs.MM, cs.CL, cs.CV, cs.LG
- 仅保留最近 7 天的论文
- 每次请求间隔 5 秒 (ArXiv courtesy)

**最新运行结果**: 172 items = 142 GitHub + 0 Semantic Scholar + 30 ArXiv papers

### 1.2 briefing.py (DONE)

- [x] 读取 `items.json` + `config.yaml`
- [x] Leader 活动和 ArXiv 论文分开呈现 (PART 1 / PART 2)
- [x] Leader 的 `note` (成就/背景) 字段作为 Bio 传入 prompt
- [x] **📄 今日论文推荐板块**: LLM 从 ArXiv 论文中选 TOP 5, 附中文摘要 + 关联分析
- [x] **🏆 今日活跃大佬档案板块** (session 3 新增): 每位活跃 leader 的详细档案卡, 包括:
  - 身份与代表成就 (基于 config.yaml note 字段)
  - 近期动向详析 (不只是"star 了 3 个 repo", 而是具体分析每个 repo 做什么、为什么重要)
  - 与我研究方向的关联
- [x] 移除旧的 "👤 大佬动态速览" (被更详细的 🏆 板块替代)
- [x] 默认模式: `prompt.md` -> 粘贴到 Claude 对话 (零成本)
- [x] `--api` 模式: 调 Anthropic API 自动生成 (需 `ANTHROPIC_API_KEY`)

**最新 prompt**: 50,888 chars, 覆盖 6 位 leader (含 Bio) + 30 篇 ArXiv 论文

### 1.3 render.py (DONE — session 3 重写)

- [x] Markdown -> HTML 转换器 (纯 Python, 无外部依赖)
- [x] **全新视觉设计** (session 3):
  - Inter + Noto Sans SC 字体 (Google Fonts)
  - 深色主题 (#0a0a0f 底色, 精心调色的层次感)
  - 板块 section header + icon 系统: 🔥红 / 🛠绿 / 📄蓝 / 🏆金 / 💰橙 / 🌟紫
  - H3 自动渲染为 card 卡片 (圆角, 悬停高亮)
  - 渐变分割线, 自定义滚动条
  - 响应式设计 (移动端适配)
- [x] 支持: 标题、列表、链接、加粗、代码块、引用、分割线

### 1.4 download.py (DONE — session 3 新增)

- [x] 从简报或 items.json 中提取 ArXiv 论文 URL
- [x] 下载 PDF 到 `papers/YYYY-MM-DD/` 日期子目录
- [x] 智能文件名: `{paper_id} - {title}.pdf`
- [x] 跳过已下载的论文 (幂等)
- [x] 两种模式:
  - `python download.py output/briefing-2026-05-01.md` — 只下载简报中推荐的论文
  - `python download.py --all` — 下载 items.json 中所有 ArXiv 论文

### 1.5 run.py (DONE — 已更新)

三种使用模式:
- `python run.py` — scrape + 生成 prompt.md (手动粘贴)
- `python run.py --api` — scrape + API 生成简报 + 渲染 HTML
- `python run.py --render` — 仅渲染已有简报为 HTML

### 1.6 Environment Setup (DONE)

- [x] `.env.example` 模板
- [x] Python 3.12 + httpx + pyyaml + anthropic

### 1.7 Validation (IN PROGRESS)

- [x] scrape.py 数据采集正常 (172 items, 含 leader_note)
- [x] briefing.py prompt 生成正常 (50,888 chars, 含 Bio + ArXiv)
- [x] render.py HTML 渲染正常 (新视觉设计, section cards)
- [x] download.py 论文下载正常 (30 篇 PDF)
- [ ] **用户首次使用完整流程, 评估简报质量**
- [ ] 连续使用 4-7 天, 验证假设

---

## File Structure (Current)

```
TrendRadar/
  Outline.md            # 实现设计大纲
  PROGRESS.md           # 本文件 — 开发进度
  config.yaml           # 27 leaders + research profile
  scrape.py             # GitHub + Semantic Scholar + ArXiv 数据抓取
  briefing.py           # 构建 prompt / 调 API 生成简报
  render.py             # Markdown -> styled HTML 渲染器
  download.py           # ArXiv 论文 PDF 下载器
  run.py                # 编排器 (三种模式)
  .env.example          # 环境变量模板
  items.json            # 抓取的原始数据 (自动生成)
  prompt.md             # 拼装好的 prompt (自动生成)
  output/               # 简报输出目录
    briefing-YYYY-MM-DD.md    # 简报 Markdown
    briefing-YYYY-MM-DD.html  # 简报 HTML (渲染后)
  papers/               # 论文 PDF 下载目录
    YYYY-MM-DD/               # 按日期分目录
```

---

## Decision Log

| Date | Decision | Reason |
|---|---|---|
| 2026-04-30 | Approach A -> C roadmap | 先验证核心循环再投入架构 |
| 2026-04-30 | Briefing-first, not scoring-first | 用户明确: 评分只是手段, 简报才是目的 |
| 2026-04-30 | Skip Approach B (web platform) | 个人工具不需要 web app 的复杂度 |
| 2026-04-30 | JSON files, no database | Approach A 是一次性原型, 优化速度不是健壮性 |
| 2026-05-01 | 拒绝添加 Elon Musk | 信号密度标准: 商业/争议信号会稀释 HCI/游戏简报质量 |
| 2026-05-01 | 27 leaders, 7 categories | 覆盖所有研究方向 + 短板补强 |
| 2026-05-01 | Prompt 文件 + 手动粘贴 (默认) | Max 套餐不含 API, 避免额外付费 |
| 2026-05-01 | 新增 ArXiv 论文抓取 | HCI 是硕士研究领域, 论文追踪是必要需求 |
| 2026-05-01 | 新增 HTML 渲染器 | 用户需要可视化友好的简报展示, 不只是纯 Markdown |
| 2026-05-01 | ArXiv 3 宽查询策略 | 避免 ArXiv API 429 限流, 5 秒间隔, 覆盖 HCI/Game/AI 三个方向 |
| 2026-05-01 | 新增大佬档案板块替代动态速览 | 用户需要详细信息来判断是否手动深入, 粗略方向不够 |
| 2026-05-01 | 新增论文 PDF 下载 | 推荐论文应该直接可读, 减少手动操作 |
| 2026-05-01 | HTML 视觉重写 | 改用 card 布局 + section icon 系统, 提升可读性和美观度 |
| 2026-05-01 | 移除 API key 依赖 | 用户使用 Max 套餐, API 需额外付费; 改为 Skill 直接生成 |
| 2026-05-01 | 封装为 /trend-radar Skill | 即插即用, 支持 `/trend-radar` 或 `/trend-radar c` 参数 |

---

## Known Issues

1. **Semantic Scholar 数据为空**: 27 位 leader 均未配置 `semantic_scholar` ID。优先级低。
2. **GitHub events 偶发断连**: 部分 leader 的 events 请求遇到断连, starred repos 正常。非阻塞。
3. **GitHub starred 无时间过滤**: 返回全部历史 star, 部分数据较老。Approach C 可优化。
4. **ArXiv 论文质量**: 关键词搜索可能返回不太相关的论文, 依赖 LLM 在简报生成时做相关性筛选。

---

## Daily Use Workflow

### 方式 1: Skill (推荐)
在 Claude Code 中输入:
```
/trend-radar
```
全自动: 抓取数据 -> 生成简报 -> 保存 -> 渲染 HTML -> 下载论文

### 方式 2: 手动脚本
```bash
cd D:/ClaudeCode/TrendRadar
python run.py                # 抓取数据 + 生成 prompt.md
# 复制 prompt.md 内容粘贴到 Claude 对话
# 保存回复到 output/briefing-YYYY-MM-DD.md
python render.py             # 渲染 HTML
python download.py output/briefing-YYYY-MM-DD.md  # 下载论文
```

---

## Notes for Future Sessions

1. **接续开发**: 读取 `Outline.md` + 本文件即可了解全部上下文
2. **config.yaml 已完成**: profile + 27 leaders
3. **核心设计原则**:
   - 监控人比监控话题更好
   - 一次 LLM 调用, 一份叙事简报
   - Approach A 是一次性的 — 优化速度, 不优化健壮性
   - 学习项目 — 可读代码优先
4. **两种简报模式**:
   - 默认: `prompt.md` -> 粘贴到 Claude 对话
   - API: `--api` -> 需要 `ANTHROPIC_API_KEY`
5. **新增功能 (session 2)**:
   - ArXiv 论文抓取 (3 宽查询, 近 7 天, 最多 30 篇)
   - HTML 渲染器, run.py 三种模式
6. **新增功能 (session 3)**:
   - 🏆 今日活跃大佬档案 — 替代旧的"动态速览", 含详细成就 + 活动分析
   - download.py — ArXiv 论文 PDF 下载 (从简报或全量)
   - HTML 视觉全面重写 (Inter 字体, card 布局, section icon, 深色主题)
   - leader_note 字段注入 prompt (Bio 信息)
7. **Session 4 重构**:
   - 彻底移除 Anthropic API key 依赖 (briefing.py, run.py, .env.example)
   - 封装为 `/trend-radar` Claude Code Skill (`~/.claude/skills/trend-radar/SKILL.md`)
   - Skill 直接在对话中生成简报 (Claude Code 本身就是 LLM, 不需要外部 API)
   - 支持参数: `/trend-radar` = Approach A, `/trend-radar c` = Approach C (待实现)
