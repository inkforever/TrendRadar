"""
TrendRadar - ArXiv Paper Downloader

Download recommended papers from a briefing file or from items.json.

Usage:
  python download.py                              # download from today's briefing
  python download.py output/briefing-2026-05-01.md  # from specific briefing
  python download.py --all                         # download all papers from items.json
"""

import json
import os
import re
import sys
from datetime import datetime

import httpx

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ITEMS_PATH = os.path.join(BASE_DIR, "items.json")
PAPERS_DIR = os.path.join(BASE_DIR, "papers")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def extract_arxiv_urls_from_briefing(briefing_path):
    """Extract ArXiv URLs from a briefing markdown file."""
    with open(briefing_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Match arxiv URLs (both abs and pdf)
    urls = re.findall(r"https?://arxiv\.org/(?:abs|pdf)/[\d.]+(?:v\d+)?", content)
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for url in urls:
        # Normalize to abs URL
        normalized = url.replace("/pdf/", "/abs/")
        if normalized not in seen:
            seen.add(normalized)
            unique.append(normalized)
    return unique


def extract_arxiv_from_items():
    """Extract all ArXiv paper info from items.json."""
    with open(ITEMS_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)

    papers = []
    for item in items:
        if item.get("source") == "arxiv":
            papers.append({
                "title": item["title"],
                "url": item["url"],
                "authors": item.get("meta", {}).get("authors", []),
                "category": item.get("meta", {}).get("category", ""),
                "date": item.get("timestamp", "")[:10],
            })
    return papers


def arxiv_url_to_pdf(url):
    """Convert an ArXiv URL to its PDF download URL."""
    # Extract paper ID from URL
    match = re.search(r"(\d{4}\.\d{4,5}(?:v\d+)?)", url)
    if match:
        paper_id = match.group(1)
        return f"https://arxiv.org/pdf/{paper_id}.pdf", paper_id
    return None, None


def sanitize_filename(title, max_len=80):
    """Create a safe filename from paper title."""
    # Remove special characters
    safe = re.sub(r'[<>:"/\\|?*]', '', title)
    safe = re.sub(r'\s+', ' ', safe).strip()
    if len(safe) > max_len:
        safe = safe[:max_len].rsplit(' ', 1)[0]
    return safe


def download_paper(pdf_url, paper_id, title, save_dir, client):
    """Download a single paper PDF."""
    filename = f"{paper_id} - {sanitize_filename(title)}.pdf"
    filepath = os.path.join(save_dir, filename)

    if os.path.exists(filepath):
        print(f"  [SKIP] Already exists: {filename}")
        return filepath

    try:
        print(f"  Downloading: {filename}")
        resp = client.get(pdf_url, follow_redirects=True, timeout=60)
        resp.raise_for_status()

        with open(filepath, "wb") as f:
            f.write(resp.content)

        size_kb = len(resp.content) / 1024
        print(f"  -> Saved ({size_kb:.0f} KB)")
        return filepath
    except Exception as e:
        print(f"  [WARN] Download failed: {e}")
        return None


def main():
    args = sys.argv[1:]
    download_all = "--all" in args

    # Create date-based subfolder
    today = datetime.now().strftime("%Y-%m-%d")
    save_dir = os.path.join(PAPERS_DIR, today)
    os.makedirs(save_dir, exist_ok=True)

    papers_to_download = []

    if download_all:
        # Download all papers from items.json
        print("Downloading ALL ArXiv papers from items.json...")
        papers = extract_arxiv_from_items()
        for p in papers:
            pdf_url, paper_id = arxiv_url_to_pdf(p["url"])
            if pdf_url:
                papers_to_download.append((pdf_url, paper_id, p["title"]))

    else:
        # Download from briefing file
        briefing_path = None
        for arg in args:
            if not arg.startswith("--") and os.path.exists(arg):
                briefing_path = arg
                break

        if briefing_path is None:
            briefing_path = os.path.join(OUTPUT_DIR, f"briefing-{today}.md")

        if not os.path.exists(briefing_path):
            print(f"Briefing not found: {briefing_path}")
            print("Usage:")
            print("  python download.py output/briefing-2026-05-01.md  (from briefing)")
            print("  python download.py --all                          (all from items.json)")
            sys.exit(1)

        print(f"Extracting ArXiv URLs from: {briefing_path}")
        urls = extract_arxiv_urls_from_briefing(briefing_path)

        if not urls:
            print("No ArXiv URLs found in briefing. Falling back to items.json...")
            papers = extract_arxiv_from_items()
            for p in papers:
                pdf_url, paper_id = arxiv_url_to_pdf(p["url"])
                if pdf_url:
                    papers_to_download.append((pdf_url, paper_id, p["title"]))
        else:
            # Match URLs back to items.json for titles
            items_by_id = {}
            if os.path.exists(ITEMS_PATH):
                papers = extract_arxiv_from_items()
                for p in papers:
                    match = re.search(r"(\d{4}\.\d{4,5})", p["url"])
                    if match:
                        items_by_id[match.group(1)] = p

            for url in urls:
                pdf_url, paper_id = arxiv_url_to_pdf(url)
                if pdf_url:
                    title = items_by_id.get(paper_id, {}).get("title", paper_id)
                    papers_to_download.append((pdf_url, paper_id, title))

    if not papers_to_download:
        print("No papers to download.")
        return

    print(f"\nDownloading {len(papers_to_download)} papers to {save_dir}/\n")

    downloaded = 0
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        for pdf_url, paper_id, title in papers_to_download:
            result = download_paper(pdf_url, paper_id, title, save_dir, client)
            if result:
                downloaded += 1

    print(f"\nDone! {downloaded}/{len(papers_to_download)} papers saved to {save_dir}/")


if __name__ == "__main__":
    main()
