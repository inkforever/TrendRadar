# TrendRadar

AI-synthesized daily intelligence briefing based on tracked research leaders.

TrendRadar monitors influential researchers across GitHub, Semantic Scholar, and ArXiv, then uses an LLM to synthesize a narrative intelligence report. The core insight: **monitoring people is a better signal than monitoring topics.** Leaders act before they publish — by watching what they star, cite, fork, and discuss, you detect trends early.

## How It Works

```
scrape all data ──> dump everything into one prompt ──> LLM writes a trend briefing
```

Data sources:
- **GitHub**: starred repos + public events for tracked leaders
- **Semantic Scholar**: recent papers by tracked leaders
- **ArXiv**: keyword-based paper search (last 7 days)

Briefing sections:
- 🔥 Hot Topics — cross-leader trend convergence
- 🛠 New Tools & Tech — repos leaders starred/forked/created
- 📄 Paper Recommendations — top 5 ArXiv papers ranked by relevance to you
- 🏆 Active Leader Profiles — detailed analysis of each leader's recent activity
- 💰 Funding & Industry Signals
- 🌟 Recommended New People to follow

## Prerequisites

- Python 3.10+
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (CLI, desktop app, or IDE extension)
- A GitHub Personal Access Token (free)

## Setup

1. **Clone the repo**

   ```bash
   git clone https://github.com/YOUR_USERNAME/TrendRadar.git
   cd TrendRadar
   ```

2. **Install Python dependencies**

   ```bash
   pip install httpx pyyaml
   ```

3. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env and add your GITHUB_TOKEN
   ```

4. **Create your config**

   ```bash
   cp config.yaml.example config.yaml
   ```

   Edit `config.yaml` to add:
   - Your research profile (identity, focus areas, keywords)
   - Leaders you want to track (15-25 recommended)
   - See `config.yaml.example` for the full schema

## Usage

### With Claude Code (recommended)

Open Claude Code in the TrendRadar directory and run:

```
/trend-radar
```

This automatically: scrapes fresh data → generates a narrative briefing → saves to `output/` → renders HTML → downloads recommended papers.

The skill is bundled in `.claude/skills/` and works automatically when you `cd` into the project.

### Manual scripts

```bash
# Scrape data
python scrape.py

# Generate the prompt (for manual paste into Claude)
python briefing.py
# Copy prompt.md content into a Claude conversation

# Render a briefing markdown to HTML
python render.py output/briefing-2026-05-02.md

# Download ArXiv papers recommended in a briefing
python download.py output/briefing-2026-05-02.md

# Download ALL scraped ArXiv papers
python download.py --all
```

### Orchestrator

```bash
python run.py           # scrape + generate prompt.md
python run.py --render  # render existing briefing to HTML
```

## Output

```
output/
  briefing-YYYY-MM-DD.md     # Markdown briefing
  briefing-YYYY-MM-DD.html   # Styled HTML (dark theme, card layout)
papers/
  YYYY-MM-DD/                # Downloaded ArXiv PDFs
```

## Adding Leaders

Use the `/leader-scout` Claude Code skill (if available) or manually add entries to `config.yaml`:

```yaml
- name: "Jane Doe"
  github: "janedoe"
  twitter: "@janedoe"
  homepage: "https://janedoe.com"
  tags: ["HCI", "VR", "interaction-design"]
  note: "MIT Professor, known for XR haptics research, CHI Best Paper 2024"
```

Tips:
- At least some leaders should have a `github` field (primary data source)
- Order leaders within each category by activity level (most active first)
- The `note` field is injected into the briefing as the leader's bio

## Architecture

This is **Approach A** — a validation prototype. Intentionally simple:
- No database (JSON files)
- No web UI
- No scheduling (run manually or via `/trend-radar`)
- Three Python files + one LLM call = one briefing

See `Outline.md` for the Approach C roadmap (agent-based architecture, SQLite, feedback loops, more data sources).

## License

MIT
