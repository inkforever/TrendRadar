"""
TrendRadar - Briefing Generator
Read items.json + config.yaml, build prompt, save to prompt.md.
User pastes prompt into Claude chat to generate the briefing.
"""

import json
import os
import sys
from datetime import datetime

import yaml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.yaml")
ITEMS_PATH = os.path.join(BASE_DIR, "items.json")
PROMPT_PATH = os.path.join(BASE_DIR, "prompt.md")


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_items():
    with open(ITEMS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_profile_section(profile):
    lines = []
    lines.append(f"Identity: {profile.get('identity', '')}")
    lines.append(f"Research areas: {', '.join(profile.get('research_areas', []))}")
    lines.append(f"Current focus: {profile.get('current_focus', '').strip()}")
    lines.append(f"Keywords: {', '.join(profile.get('keywords', []))}")
    lines.append(f"Game interests: {', '.join(profile.get('game_interests', []))}")
    lines.append(f"Growth areas (flag, don't filter): {', '.join(profile.get('growth_areas', []))}")
    lines.append(f"AI tracking categories: {', '.join(profile.get('ai_tracking', []))}")
    return "\n".join(lines)


def build_data_section(items):
    """Build leader activity section (excludes ArXiv papers)."""
    by_leader = {}
    for item in items:
        if item.get("source") == "arxiv":
            continue
        leader = item["leader"]
        if leader not in by_leader:
            by_leader[leader] = {
                "tags": item.get("leader_tags", []),
                "note": item.get("leader_note", ""),
                "items": [],
            }
        by_leader[leader]["items"].append(item)

    lines = []
    for leader, data in by_leader.items():
        tags_str = ", ".join(data["tags"])
        lines.append(f"--- {leader} (tags: {tags_str}) ---")
        if data["note"]:
            lines.append(f"Bio: {data['note']}")
        for item in data["items"]:
            lines.append(f"[{item['source']}] {item['title']}")
            if item.get("content"):
                lines.append(item["content"][:300])
            if item.get("url"):
                lines.append(f"URL: {item['url']}")
            if item.get("timestamp"):
                lines.append(f"Time: {item['timestamp']}")
            meta = item.get("meta", {})
            if meta.get("stars") and meta["stars"] > 100:
                lines.append(f"Stars: {meta['stars']}  Language: {meta.get('language', '')}")
            lines.append("")
        lines.append("")

    return "\n".join(lines)


def build_arxiv_section(items):
    """Build ArXiv papers section."""
    arxiv_items = [i for i in items if i.get("source") == "arxiv"]
    if not arxiv_items:
        return "(No recent ArXiv papers found)"

    lines = []
    for item in arxiv_items:
        authors = ", ".join(item.get("meta", {}).get("authors", [])[:5])
        category = item.get("meta", {}).get("category", "")
        lines.append(f"Title: {item['title']}")
        lines.append(f"Authors: {authors}")
        lines.append(f"Category: {category}")
        if item.get("content"):
            lines.append(f"Abstract: {item['content'][:400]}")
        lines.append(f"URL: {item.get('url', '')}")
        lines.append(f"Date: {item.get('timestamp', '')[:10]}")
        lines.append("")

    return "\n".join(lines)


BRIEFING_PROMPT = """You are a research intelligence analyst specializing in HCI (Human-Computer
Interaction) and electronic gaming research. You produce a daily intelligence
briefing for a researcher.

RESEARCHER PROFILE:
{profile}

=== PART 1: TRACKED LEADERS' RECENT ACTIVITY ===
(Below is everything that {leader_count} tracked researchers did recently, grouped by person)

{data}

=== PART 2: RECENT ARXIV PAPERS ===
(Below are {arxiv_count} recent papers from ArXiv in relevant categories: cs.HC, cs.AI, cs.GR, cs.CL, cs.CV, cs.LG)

{arxiv_data}

Based on ALL the data above, write a daily intelligence briefing in Chinese (中文).
Use the following structure:

## 🔥 当前热点方向
What topics or themes appeared multiple times across different leaders?
Are multiple unconnected people converging on the same thing?
Name the specific leaders and what they did. If no clear trend, say so honestly.

## 🛠 值得关注的新工具与新技术
New repos, libraries, frameworks, or tools that leaders starred, forked, or created.
For each one: what it does, why it might matter, who starred/forked it.

## 📄 今日论文推荐
From the ArXiv papers above, select the TOP 5 most relevant papers to the researcher's
profile and current focus. For each paper:
- **标题**: paper title
- **作者**: first 3 authors
- **摘要**: 2-3 句中文总结 (不是翻译摘要, 而是用你自己的话解释这篇论文做了什么、为什么重要)
- **与我的关联**: explain the specific connection to the researcher's focus areas
  (meta-interaction, LLM narrative, XR, game design, scaffold system, etc.)
- **URL**: paper link

Prioritize papers that:
1. Directly relate to the researcher's current focus (meta-interaction, LLM + game engine)
2. Present novel methods in HCI / XR / VR interaction
3. Introduce new AI tools or techniques applicable to game design
4. Touch on the researcher's growth areas (narrative design, visual design)

## 🏆 今日活跃大佬档案
For EACH leader who has activity data today, create a detailed profile card.
Use the Bio information provided in the data AND their recent activity to write:

For each active leader:
### [Leader Name]
- **身份**: who they are, their affiliation, their role (from Bio field)
- **代表成就**: their most notable projects, papers, awards, or contributions
  (from Bio field — expand with your knowledge if you know more about them)
- **近期动向详析**: analyze their recent activity IN DETAIL. Don't just say
  "starred 3 repos related to X" — explain WHAT those repos do, WHY they might
  matter, and what this activity pattern SUGGESTS about where this leader is heading.
  For push events: what are they working on? What do the commit messages reveal?
  For starred repos: what specific tools/frameworks caught their eye? Give URLs.
- **与我的关联**: how does this leader's work and recent activity connect to the
  researcher's focus areas? Be specific.

This section should give the reader enough detail to decide whether to manually
explore each leader's activity further. Think of it as a research intelligence
dossier, not a summary.

## 💰 资金与行业信号
Any signals about where money or institutional attention is flowing.
Infer from: corporate lab paper output, startup-related repos, industry
partnerships visible in affiliations. If no clear signals today, skip this section.

## 🌟 推荐关注的新人物
If any data references people not currently tracked (paper co-authors,
repo contributors, cited researchers) who appear relevant, recommend them.
Include: name, affiliation if visible, why they seem worth following.

Rules:
- Be specific. Name names. Link URLs. Cite evidence.
- Prioritize signal over noise. If today is quiet, say so. Don't inflate.
- If a section has nothing meaningful, write "今日无明显信号" and move on.
- The 🏆 section should be the most detailed — give enough context for the reader
  to decide whether to dig deeper into each leader's work.
- Output the briefing in well-formatted Markdown.
"""


def build_prompt(profile, items):
    """Assemble the complete prompt from profile and items."""
    profile_text = build_profile_section(profile)
    data_text = build_data_section(items)
    arxiv_text = build_arxiv_section(items)

    leaders_with_data = len(set(
        item["leader"] for item in items if item.get("source") != "arxiv"
    ))
    arxiv_count = sum(1 for item in items if item.get("source") == "arxiv")

    prompt = BRIEFING_PROMPT.format(
        profile=profile_text,
        leader_count=leaders_with_data,
        data=data_text,
        arxiv_count=arxiv_count,
        arxiv_data=arxiv_text,
    )

    # Truncate if too long
    if len(prompt) > 400_000:
        print(f"  [WARN] Prompt too long ({len(prompt)} chars), truncating to 5 items per leader")
        non_arxiv = [i for i in items if i.get("source") != "arxiv"]
        by_leader = {}
        for item in non_arxiv:
            leader = item["leader"]
            if leader not in by_leader:
                by_leader[leader] = []
            by_leader[leader].append(item)
        truncated = []
        for leader_items in by_leader.values():
            truncated.extend(leader_items[:5])
        truncated.extend(i for i in items if i.get("source") == "arxiv")
        data_text = build_data_section(truncated)
        arxiv_text = build_arxiv_section(truncated)
        prompt = BRIEFING_PROMPT.format(
            profile=profile_text,
            leader_count=leaders_with_data,
            data=data_text,
            arxiv_count=arxiv_count,
            arxiv_data=arxiv_text,
        )

    return prompt


def main():
    config = load_config()
    profile = config.get("profile", {})
    items = load_items()
    print(f"TrendRadar Briefing — {len(items)} items from items.json")

    if not items:
        print("No items to brief on. Run scrape.py first.")
        return

    prompt = build_prompt(profile, items)

    with open(PROMPT_PATH, "w", encoding="utf-8") as f:
        f.write(prompt)

    print(f"\nPrompt saved to {PROMPT_PATH} ({len(prompt)} chars)")
    print("\nNext steps:")
    print("  1. Copy the content of prompt.md")
    print("  2. Paste into Claude chat")
    print("  3. Save the response as output/briefing-YYYY-MM-DD.md")
    print("  4. Run: python render.py")


if __name__ == "__main__":
    main()
