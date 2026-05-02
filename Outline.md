# TrendRadar - Implementation Brief

> Personalized Research Intelligence Briefing for HCI & Gaming
> Design doc: `~/.gstack/projects/ClaudeCode/12845-unknown-design-20260430-204842.md`

## Core Concept

TrendRadar monitors influential researchers across multiple sources, aggregates their activity, and uses LLM to synthesize a daily **intelligence briefing** — not a ranked list of items, but a narrative report about what's happening in the field.

The core insight: **monitoring people is a better signal than monitoring topics.** Leaders act before they publish. By watching what they star, cite, fork, and discuss, you detect trends weeks before they hit conferences.

**This is a learning project.** The user is building skills while solving a real problem. Prefer readable code over clever code.

## Architecture: Aggregate -> Synthesize -> Narrate

```
scrape all data ──> dump everything into one prompt ──> LLM writes a trend briefing
```

No per-item scoring. No ranking system. The LLM sees ALL the data at once and produces a narrative intelligence report. One call, one briefing.

## Approach A: Validation Prototype (3 days)

Purpose: validate whether an AI-synthesized trend briefing from tracked researchers tells you things you didn't know. If the briefing surfaces a trend before your afternoon tea group mentions it, the hypothesis is validated.

**Approach A is disposable.** Don't optimize for robustness or maintainability. Optimize for speed to first useful output.

### File Structure

```
TrendRadar/
  Outline.md            # this file
  config.yaml           # leaders + research profile
  scrape.py             # fetch GitHub + Semantic Scholar -> items.json
  briefing.py           # read items.json, one LLM call -> briefing markdown
  run.py                # orchestrator: scrape -> briefing -> open browser
  items.json            # raw scraped data (auto-generated)
  output/               # daily briefing files
  .env                  # API keys
```

No database. No package structure. No tests. JSON files as the data store.

### config.yaml

Leaders and research profile in one file:

```yaml
# === Your Research Profile ===
profile:
  research_areas: ["HCI", "electronic gaming", "interaction design"]
  current_focus: "AI-assisted game design tools"
  keywords: ["LLM agents", "procedural generation", "user study methods"]
  language: "Chinese"  # briefing language

# === Tracked Leaders ===
# All source fields are optional. Scrapers skip missing sources.
# To find Semantic Scholar Author IDs:
#   Search https://www.semanticscholar.org/ -> ID is in the author URL
leaders:
  - name: "Example Researcher"
    github: "example-user"
    semantic_scholar: "12345678"
    tags: ["HCI", "interaction-design"]

  # Add 15-25 more leaders here.
  # Start with: CHI best paper authors, GDC speakers,
  # SIGGRAPH/UIST keynotes, key GitHub contributors.
  # Ask your peers: "who should I be following?"
```

### Day 1: scrape.py

Two functions, one file. Fetch raw data from tracked leaders.

**`scrape_github(leaders)`**
- For each leader with a `github` field:
  - GET `https://api.github.com/users/{username}/starred?per_page=30&sort=created`
    - Extract: repo name, description, URL, language, stars count
  - GET `https://api.github.com/users/{username}/events/public?per_page=30`
    - Filter for: `WatchEvent`, `CreateEvent`, `ForkEvent`, `PushEvent`
    - Extract: event type, repo name, description, timestamp
- Auth: `GITHUB_TOKEN` env var (GitHub Personal Access Token, free)
- If a request fails: `print(f"Failed for {username}: {e}")`, skip, continue

**`scrape_semantic(leaders)`**
- For each leader with a `semantic_scholar` field:
  - GET `https://api.semanticscholar.org/graph/v1/author/{authorId}/papers?fields=title,abstract,url,year,publicationDate,externalIds&limit=10`
    - Filter: papers from the last 30 days only
    - Extract: title, abstract, URL, publication date, venue
- Rate limit: 3-second delay between requests (~60 seconds total for 20 leaders)
- If a request fails: print, skip, continue

**Output:** Write all items to `items.json`:
```json
[
  {
    "leader": "Alice Smith",
    "leader_tags": ["HCI", "interaction-design"],
    "source": "github_star",
    "title": "awesome-hci-toolkit",
    "content": "A curated list of HCI research tools and frameworks",
    "url": "https://github.com/...",
    "timestamp": "2026-05-01T08:30:00Z"
  },
  ...
]
```

**Day 1 validation:** Run `scrape.py`, open `items.json`, see real data. If the data looks like useful signals, continue. If APIs are broken or data is garbage, you've learned that in one day.

### Day 2: briefing.py

One file. Read all scraped data, make one Claude Sonnet call, write the briefing.

**The prompt:**

```
You are a research intelligence analyst specializing in HCI (Human-Computer
Interaction) and electronic gaming research. You produce a daily intelligence
briefing for a researcher.

RESEARCHER PROFILE:
Research areas: {research_areas}
Current focus: {current_focus}
Keywords: {keywords}

TRACKED LEADERS AND THEIR RECENT ACTIVITY:
(Below is everything that {N} tracked researchers did recently, grouped by person)

{for each leader with items:}
--- {leader_name} (tags: {tags}) ---
{for each item:}
[{source}] {title}
{content preview, max 300 chars}
URL: {url}
Time: {timestamp}
{end for}
{end for}

Based on this data, write a daily intelligence briefing in Chinese (中文).
Use the following structure:

## 🔥 当前热点方向
What topics or themes appeared multiple times across different leaders?
Are multiple unconnected people converging on the same thing?
Name the specific leaders and what they did. If no clear trend, say so honestly.

## 🛠 值得关注的新工具与新技术
New repos, libraries, frameworks, or tools that leaders starred, forked, or created.
For each one: what it does, why it might matter, who starred/forked it.

## 💰 资金与行业信号
Any signals about where money or institutional attention is flowing.
Infer from: corporate lab paper output, startup-related repos, industry
partnerships visible in affiliations. If no clear signals today, skip this section.

## 📄 与我研究方向相关的论文
Papers from tracked leaders that connect to the researcher's profile.
For each: title, authors, 2-sentence summary, explain the specific connection
to the researcher's focus areas. Include URL.

## 👤 大佬动态速览
Interesting or unusual behavior from specific leaders.
Example: "Dr. X, who normally works on haptics, just starred 3 NLP repos.
Direction shift worth watching."
Focus on UNUSUAL activity, not routine.

## 🌟 推荐关注的新人物
If any scraped data references people not currently tracked (paper co-authors,
repo contributors, cited researchers) who appear relevant, recommend them.
Include: name, affiliation if visible, why they seem worth following.

Rules:
- Be specific. Name names. Link URLs. Cite evidence.
- Prioritize signal over noise. If today is quiet, say so. Don't inflate.
- If a section has nothing meaningful, write "今日无明显信号" and move on.
- Write concisely. The entire briefing should be readable in 5-10 minutes.
```

**Implementation:**
1. Read `items.json` and `config.yaml`
2. Build the prompt by grouping items by leader
3. Call `claude-sonnet-4-6` with the assembled prompt
4. Write the response to `output/briefing-{YYYY-MM-DD}.md`

**Token budget:** ~20 leaders x ~5 items each x ~100 tokens per item = ~10K input tokens. Sonnet response ~2K tokens. Total cost per run: ~$0.04.

**If the prompt is too long** (over 100K tokens from very active leaders): truncate each leader's items to the 5 most recent. The LLM doesn't need every commit message.

**Day 2 validation:** Read the generated briefing. Does it tell you something you didn't know? Does the structure make sense? Tune the prompt if needed.

### Day 3: run.py + polish

**`run.py`** — 10 lines:

```python
import subprocess, webbrowser, datetime, os

print("Scraping...")
subprocess.run(["python", "scrape.py"], check=True)

print("Generating briefing...")
subprocess.run(["python", "briefing.py"], check=True)

today = datetime.date.today().isoformat()
path = os.path.abspath(f"output/briefing-{today}.md")
print(f"Done: {path}")
webbrowser.open(path)
```

Or render Markdown to simple HTML if you want a nicer look. But `.md` files open fine in VS Code or any Markdown viewer.

**Day 3 validation:** Run `python run.py`. Browser opens with today's briefing. Read it over coffee. Does this feel like a superpower?

### Days 4-7: Daily Use

Run `python run.py` manually every morning. No scheduling, no automation.

Observe:
- Do you open it every day, or forget by day 3?
- Which sections are useful? Which are filler?
- Does it ever surface something before your peers mention it?
- Are there leaders you wish you had added?
- Is the briefing quality good enough, or does the prompt need tuning?

**This week of manual use IS the validation.**

## Environment Variables

```
GITHUB_TOKEN=ghp_xxxxx           # required: GitHub Personal Access Token (free)
ANTHROPIC_API_KEY=sk-ant-xxxxx   # required: for Claude API
```

Optional:
```
SEMANTIC_SCHOLAR_API_KEY=xxxxx   # for higher Semantic Scholar rate limits
```

## Dependencies

```
pip install httpx pyyaml anthropic
```

That's it. Three packages.

---

## Approach C: Agent Evolution (after validation)

Only start after using Approach A daily for 1-2 weeks and confirming the briefing is useful.

### What changes from A to C

| Approach A | Approach C |
|---|---|
| Fixed scrape list | Source agents decide what to explore |
| Two sources (GitHub + Semantic Scholar) | Multiple sources (+ YouTube, Twitter, blogs, conferences) |
| One big prompt, one call | Curator agent with tool_use, multi-step reasoning |
| Static research profile | Interest profile evolves from feedback |
| No social graph | Trend Seismograph: detect convergence patterns |
| Manual `python run.py` | Scheduled automation, maybe a simple web UI |
| JSON files | SQLite or similar persistent storage |
| No feedback loop | Explicit + implicit feedback drives personalization |

### What carries forward from A to C

- `config.yaml` structure (leaders + profile)
- API integration patterns (GitHub, Semantic Scholar)
- The briefing prompt (becomes the curator agent's core instruction)
- The briefing sections structure (validated through daily use)

### Phase C Architecture Sketch

```
Source Agents (one per platform)
  ├── GitHub Agent: fetch + explore (can check followers, trending repos)
  ├── Semantic Scholar Agent: fetch + expand (follow citations, co-authors)
  ├── YouTube Agent: channel RSS + transcript analysis
  ├── Twitter Agent: if API access available
  └── Blog/RSS Agent: personal sites, newsletters
       │
       ▼
  Aggregated Data Store (SQLite)
       │
       ▼
  Curator Agent (Claude Sonnet with tool_use)
  - Reads all new data + user profile + feedback history
  - Calls tools: query_feedback(), get_leader_clusters(), detect_convergence()
  - Writes the daily briefing as a coherent narrative
  - Suggests new leaders, flags unusual patterns
       │
       ▼
  Delivery (HTML file / email / local web page)
       │
       ▼
  Feedback Loop
  - User rates sections/items
  - LLM updates interest profile (profile_state.json)
  - Weights adjust for next briefing
```

### Trend Seismograph (built into curator agent)

In Approach A, the LLM already does convergence detection via the prompt ("are multiple unconnected people converging on the same thing?"). In Approach C, this becomes explicit:

- Track per-artifact interactions in the database (which leaders touched which items)
- Daily query: find artifacts with interactions from >= 3 leaders spanning >= 3 tag groups within 72 hours
- Pass convergent signals to the curator agent as a priority section

### Source Agent Behavior

Each source agent is a Claude API call with `tool_use`. Unlike the Approach A scrapers (fixed crawl list), agents can:
- Check a leader's followers if they notice unusual star patterns
- Expand an arXiv/Semantic Scholar search when a new keyword cluster emerges
- Follow citation chains when a paper is starred by multiple leaders
- Decide to scrape a conference proceedings page if multiple leaders published there

### Interest Profile Evolution

- Phase A: static `config.yaml`, manually edited
- Phase C: `profile_state.json` updated by the LLM after each feedback cycle
  - Contains: weighted topic keywords, preferred authors, research direction drift notes
  - User can always override via `config.yaml` (takes precedence)
  - Migration: LLM reads old profile + accumulated feedback, writes new profile

## Open Questions (resolve during Approach A usage)

1. **Briefing length:** Is 5-10 minutes of reading the right target? Maybe 3 minutes is better for a morning scan, with a "deep dive" section at the end.
2. **Quiet days:** Current prompt says "don't inflate." But if 3 days in a row are quiet, maybe aggregate into a weekly summary instead.
3. **Leader count sweet spot:** 20? 50? 100? More leaders = more signal but also more noise. Find the balance during daily use.
4. **Which sections are actually useful?** Track which sections you skip and which you read carefully. Cut the useless ones in Approach C.
