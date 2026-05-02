---
name: trend-radar
description: |
  Generate a daily research intelligence briefing by scraping GitHub, Semantic Scholar,
  and ArXiv data for tracked leaders, then synthesizing a narrative report.
  Supports two approaches: A (validation prototype) and C (agent evolution, future).
  Use when asked to "run TrendRadar", "generate briefing", "今日简报", or "trend radar".
triggers:
  - run TrendRadar
  - trend radar
  - generate briefing
  - 今日简报
  - 跑一下TrendRadar
  - daily briefing
  - 帮我跑一下TrendRadar
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Agent
  - WebSearch
  - WebFetch
---

# /trend-radar

Generate a personalized daily research intelligence briefing.

## Arguments

- No argument or `a` → **Approach A**: scrape data, generate briefing in this conversation
- `c` → **Approach C** (future): agent-based multi-source intelligence pipeline

## Approach A Workflow

### Step 0: Locate project

The TrendRadar project root is the current working directory (where this skill lives).
All paths below are relative to this root.

Required files:
- `config.yaml` — leader list + researcher profile
- `scrape.py` — data scraper
- `briefing.py` — prompt builder (reference only, we generate the briefing directly)
- `render.py` — HTML renderer
- `download.py` — ArXiv PDF downloader

If `config.yaml` is missing, tell the user to copy from `config.yaml.example` and customize it.
If any Python files are missing, tell the user and stop.

### Step 1: Scrape data

Run the scraper to collect fresh data:

```bash
python scrape.py
```

This fetches:
- GitHub starred repos + public events for leaders with `github` field
- Semantic Scholar recent papers for leaders with `semantic_scholar` field
- ArXiv papers matching the researcher's keywords (last 7 days)

Output: `items.json`

If scraping fails entirely, stop and report. Partial failures (some leaders skipped) are fine.

### Step 2: Read data and config

Read these files:
- `items.json` — scraped data
- `config.yaml` — researcher profile + leader list

### Step 3: Generate the briefing

Using ALL the data from items.json and the researcher profile from config.yaml,
generate the briefing **directly in this conversation**. No API call needed —
you ARE the LLM.

Check config.yaml `profile.language` field for the output language.
If "Chinese", write in 中文. If "English", write in English.

The briefing must follow this structure:

---

## 🔥 当前热点方向 / Current Hot Topics
What topics or themes appeared multiple times across different leaders?
Are multiple unconnected people converging on the same thing?
Name the specific leaders and what they did. If no clear trend, say so honestly.

## 🛠 值得关注的新工具与新技术 / Notable New Tools & Tech
New repos, libraries, frameworks, or tools that leaders starred, forked, or created.
For each one: what it does, why it might matter, who starred/forked it.

## 📄 今日论文推荐 / Paper Recommendations
From the ArXiv papers, select the TOP 5 most relevant papers to the researcher's
profile and current focus. For each paper:
- **标题/Title**: paper title
- **作者/Authors**: first 3 authors
- **摘要/Summary**: 2-3 sentence summary in your own words
- **与我的关联/Relevance**: the specific connection to the researcher's focus areas
- **URL**: paper link

Prioritize papers that directly relate to the researcher's `current_focus` and `keywords`.

## 🏆 今日活跃大佬档案 / Active Leader Profiles
For EACH leader who has activity data, create a detailed profile card:
### [Leader Name]
- **身份/Identity**: who they are, affiliation, role (from the `note` field in config.yaml)
- **代表成就/Notable Work**: most notable projects, papers, awards
- **近期动向详析/Recent Activity Analysis**: analyze recent activity IN DETAIL. Don't just say "starred 3
  repos related to X" — explain WHAT those repos do, WHY they might matter, and
  what this pattern SUGGESTS about where the leader is heading. Give URLs.
- **与我的关联/Relevance**: how does this connect to the researcher's focus areas?

This section should give enough detail to decide whether to dig deeper.

## 💰 资金与行业信号 / Funding & Industry Signals
Signals about where money or institutional attention is flowing.
If no clear signals, write "今日无明显信号" / "No clear signals today".

## 🌟 推荐关注的新人物 / Recommended New People
People not currently tracked who appear relevant.
Include: name, affiliation, why they seem worth following.

---

**Rules for the briefing:**
- Be specific. Name names. Link URLs. Cite evidence.
- Prioritize signal over noise. If today is quiet, say so. Don't inflate.
- If a section has nothing meaningful, say so explicitly and move on.
- The 🏆 section should be the most detailed.
- The briefing should be readable in 5-10 minutes.

### Step 4: Save and render

After generating the briefing:

1. Save the briefing to `output/briefing-{YYYY-MM-DD}.md`
   (prepend `# TrendRadar Daily Briefing — {YYYY-MM-DD}\n\n` as the header)

2. Render to HTML:
```bash
python render.py output/briefing-{YYYY-MM-DD}.md
```

3. Download recommended ArXiv papers:
```bash
python download.py output/briefing-{YYYY-MM-DD}.md
```

4. Tell the user: briefing saved, HTML rendered, papers downloaded.

### Step 5: Done

Report a brief summary:
- How many leaders had activity
- How many ArXiv papers were scraped
- How many papers were downloaded
- Path to the HTML briefing

---

## Approach C Workflow

**Status: NOT YET IMPLEMENTED**

When invoked with argument `c`, inform the user:

> Approach C (Agent Evolution) is not yet implemented.
>
> Per the Outline.md design, Approach C should only start after using Approach A
> daily for 1-2 weeks and confirming the briefing is useful.
>
> Key differences from Approach A:
> - Source Agents: one intelligent agent per platform, can autonomously explore
> - Curator Agent: multi-step reasoning curator replaces one-shot prompt
> - Trend Seismograph: detect 3+ unrelated leaders converging on the same thing within 72h
> - Feedback loop: user ratings drive interest profile evolution
> - Data store: SQLite replaces JSON files
> - More sources: YouTube, Twitter, blogs, conferences
>
> Ready to start developing Approach C?

If the user confirms, read `Outline.md` for the full Approach C architecture spec
and begin implementation planning.

---

## Error Handling

- If `scrape.py` fails: show the error, suggest checking GITHUB_TOKEN in `.env`
- If `items.json` is empty or missing: tell the user to run scrape first
- If `render.py` fails: still report the .md path as fallback
- If `download.py` fails: note it but don't block the briefing delivery
- If config.yaml is missing: tell the user to copy from config.yaml.example

## Important Rules

- **Always scrape fresh data** — don't reuse stale items.json
- **Generate the briefing directly** — you are the LLM, no API needed
- **Respect the language setting** — check config.yaml profile.language
- **Don't skip sections** — if a section has no signal, say so explicitly
- **The 🏆 section is the priority** — spend the most detail here
