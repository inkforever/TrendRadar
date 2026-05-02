"""
TrendRadar - Data Scraper
Fetch GitHub activity + Semantic Scholar papers + ArXiv papers for tracked leaders.
Output: items.json
"""

import json
import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import httpx
import yaml

BASE_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE_DIR, "config.yaml")
OUTPUT_PATH = os.path.join(BASE_DIR, "items.json")

# Load .env file if present
_env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
SEMANTIC_SCHOLAR_API_KEY = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "")

GITHUB_HEADERS = {"Accept": "application/vnd.github.v3+json"}
if GITHUB_TOKEN:
    GITHUB_HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

SEMANTIC_HEADERS = {}
if SEMANTIC_SCHOLAR_API_KEY:
    SEMANTIC_HEADERS["x-api-key"] = SEMANTIC_SCHOLAR_API_KEY


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def scrape_github(leaders, client):
    """Fetch starred repos and public events for each leader with a GitHub account."""
    items = []

    for leader in leaders:
        username = leader.get("github")
        if not username:
            continue

        name = leader["name"]
        tags = leader.get("tags", [])
        note = leader.get("note", "")
        print(f"  GitHub: {name} (@{username})")

        # --- Starred repos (recent 30) ---
        try:
            resp = client.get(
                f"https://api.github.com/users/{username}/starred",
                params={"per_page": 30, "sort": "created", "direction": "desc"},
                headers={**GITHUB_HEADERS, "Accept": "application/vnd.github.v3.star+json"},
            )
            resp.raise_for_status()
            for star in resp.json():
                repo = star.get("repo", star)  # star+json wraps in {starred_at, repo}
                starred_at = star.get("starred_at", "")
                items.append({
                    "leader": name,
                    "leader_tags": tags,
                    "leader_note": note,
                    "source": "github_star",
                    "title": repo.get("full_name", ""),
                    "content": repo.get("description") or "",
                    "url": repo.get("html_url", ""),
                    "timestamp": starred_at,
                    "meta": {
                        "language": repo.get("language"),
                        "stars": repo.get("stargazers_count", 0),
                        "topics": repo.get("topics", []),
                    },
                })
        except Exception as e:
            print(f"    [WARN] starred failed: {e}")

        # --- Public events (recent 30) ---
        try:
            resp = client.get(
                f"https://api.github.com/users/{username}/events/public",
                params={"per_page": 30},
                headers=GITHUB_HEADERS,
            )
            resp.raise_for_status()
            for event in resp.json():
                etype = event.get("type", "")
                if etype not in ("WatchEvent", "CreateEvent", "ForkEvent", "PushEvent"):
                    continue

                repo_name = event.get("repo", {}).get("name", "")
                payload = event.get("payload", {})

                # Build content based on event type
                if etype == "PushEvent":
                    commits = payload.get("commits", [])
                    content = "; ".join(c.get("message", "")[:80] for c in commits[:3])
                elif etype == "CreateEvent":
                    content = f"Created {payload.get('ref_type', '')} {payload.get('ref', '') or ''}: {payload.get('description', '') or ''}"
                elif etype == "ForkEvent":
                    content = f"Forked to {payload.get('forkee', {}).get('full_name', '')}"
                else:
                    content = f"Starred {repo_name}"
                    # Skip WatchEvent if we already have it from starred
                    continue

                items.append({
                    "leader": name,
                    "leader_tags": tags,
                    "leader_note": note,
                    "source": f"github_{etype.replace('Event', '').lower()}",
                    "title": repo_name,
                    "content": content[:300],
                    "url": f"https://github.com/{repo_name}",
                    "timestamp": event.get("created_at", ""),
                })
        except Exception as e:
            print(f"    [WARN] events failed: {e}")

    return items


def scrape_semantic_scholar(leaders, client):
    """Fetch recent papers for each leader with a Semantic Scholar ID."""
    items = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)

    for leader in leaders:
        author_id = leader.get("semantic_scholar")
        if not author_id:
            continue

        name = leader["name"]
        tags = leader.get("tags", [])
        print(f"  Semantic Scholar: {name} (ID:{author_id})")

        try:
            resp = client.get(
                f"https://api.semanticscholar.org/graph/v1/author/{author_id}/papers",
                params={
                    "fields": "title,abstract,url,year,publicationDate,externalIds,venue",
                    "limit": 10,
                },
                headers=SEMANTIC_HEADERS,
            )
            resp.raise_for_status()
            data = resp.json()

            for paper in data.get("data", []):
                pub_date = paper.get("publicationDate")
                if pub_date:
                    try:
                        pd = datetime.strptime(pub_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                        if pd < cutoff:
                            continue
                    except ValueError:
                        pass

                abstract = paper.get("abstract") or ""
                items.append({
                    "leader": name,
                    "leader_tags": tags,
                    "source": "semantic_scholar",
                    "title": paper.get("title", ""),
                    "content": abstract[:300],
                    "url": paper.get("url", ""),
                    "timestamp": pub_date or "",
                    "meta": {
                        "venue": paper.get("venue"),
                        "year": paper.get("year"),
                    },
                })
        except Exception as e:
            print(f"    [WARN] failed: {e}")

        # Rate limit: 3 second delay between requests
        time.sleep(3)

    return items


def scrape_arxiv(profile, client):
    """Fetch recent ArXiv papers matching the researcher's interests.

    Uses 3 focused queries (HCI, game, AI) instead of many keyword queries
    to stay within ArXiv's rate limits (3s between requests).
    """
    items = []
    seen_ids = set()

    # 3 broad queries covering the user's 3 research areas
    queries = [
        {
            "name": "HCI + XR + VR",
            "query": 'all:"human computer interaction" OR all:"virtual reality" OR all:"augmented reality" OR all:"human AI interaction"',
            "cats": ["cs.HC"],
        },
        {
            "name": "Game + Procedural Generation",
            "query": 'all:"game design" OR all:"procedural generation" OR all:"game engine" OR all:"level design"',
            "cats": ["cs.HC", "cs.AI", "cs.GR"],
        },
        {
            "name": "LLM + Generative AI Tools",
            "query": 'all:"large language model" OR all:"generative AI" OR all:"AI agent" OR all:"code generation"',
            "cats": ["cs.AI", "cs.CL", "cs.HC"],
        },
    ]

    for q in queries:
        cat_filter = " OR ".join(f"cat:{c}" for c in q["cats"])
        search_query = f"({q['query']}) AND ({cat_filter})"

        print(f"    Query: {q['name']}")

        try:
            resp = client.get(
                "https://export.arxiv.org/api/query",
                params={
                    "search_query": search_query,
                    "sortBy": "submittedDate",
                    "sortOrder": "descending",
                    "max_results": 15,
                },
                timeout=60,
            )
            resp.raise_for_status()

            root = ET.fromstring(resp.text)
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            count = 0
            for entry in root.findall("atom:entry", ns):
                arxiv_id = entry.find("atom:id", ns).text.strip()
                if arxiv_id in seen_ids:
                    continue
                seen_ids.add(arxiv_id)

                title = entry.find("atom:title", ns).text.strip()
                title = re.sub(r"\s+", " ", title)

                summary_el = entry.find("atom:summary", ns)
                summary = re.sub(r"\s+", " ", summary_el.text.strip()) if summary_el is not None else ""

                published = entry.find("atom:published", ns).text.strip()

                # Filter: only papers from last 7 days
                try:
                    pub_dt = datetime.strptime(published[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if pub_dt < datetime.now(timezone.utc) - timedelta(days=7):
                        continue
                except ValueError:
                    pass

                authors = [
                    a.find("atom:name", ns).text
                    for a in entry.findall("atom:author", ns)
                ]

                primary_cat = ""
                cat_el = entry.find("{http://arxiv.org/schemas/atom}primary_category")
                if cat_el is not None:
                    primary_cat = cat_el.get("term", "")

                pdf_url = arxiv_id
                for link in entry.findall("atom:link", ns):
                    if link.get("title") == "pdf":
                        pdf_url = link.get("href", arxiv_id)
                        break

                items.append({
                    "leader": "ArXiv",
                    "leader_tags": ["paper", primary_cat],
                    "source": "arxiv",
                    "title": title,
                    "content": summary[:500],
                    "url": pdf_url,
                    "timestamp": published,
                    "meta": {
                        "authors": authors[:5],
                        "category": primary_cat,
                        "query_group": q["name"],
                    },
                })
                count += 1

            print(f"      -> {count} recent papers")

        except Exception as e:
            print(f"    [WARN] ArXiv query failed for [{q['name']}]: {e}")

        # ArXiv courtesy delay: 5 seconds between requests
        time.sleep(5)

    items.sort(key=lambda x: x["timestamp"], reverse=True)
    return items[:30]


def main():
    config = load_config()
    leaders = config.get("leaders", [])
    profile = config.get("profile", {})
    print(f"TrendRadar Scraper — {len(leaders)} leaders")

    all_items = []

    with httpx.Client(timeout=30, follow_redirects=True) as client:
        print("\n[1/3] Scraping GitHub...")
        github_items = scrape_github(leaders, client)
        all_items.extend(github_items)
        print(f"  -> {len(github_items)} items")

        print("\n[2/3] Scraping Semantic Scholar...")
        scholar_items = scrape_semantic_scholar(leaders, client)
        all_items.extend(scholar_items)
        print(f"  -> {len(scholar_items)} items")

        print("\n[3/3] Scraping ArXiv...")
        arxiv_items = scrape_arxiv(profile, client)
        all_items.extend(arxiv_items)
        print(f"  -> {len(arxiv_items)} papers")

    print(f"\nTotal: {len(all_items)} items")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)

    print(f"Written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
