"""
TrendRadar - HTML Renderer
Convert briefing markdown to a styled HTML page.

Usage:
  python render.py                                  # render today's briefing
  python render.py output/briefing-2026-05-01.md    # render specific file
"""

import os
import re
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  :root {{
    --bg: #0a0a0f;
    --bg-elevated: #12121a;
    --surface: #1a1a26;
    --surface-hover: #22222f;
    --border: #2a2a3a;
    --border-subtle: #1e1e2e;
    --text: #e8e8f0;
    --text-secondary: #a0a0b8;
    --text-muted: #6a6a80;
    --accent: #6c9fff;
    --accent-dim: #4a7acc;
    --accent-glow: #6c9fff18;
    --fire: #ff6b6b;
    --fire-dim: #ff6b6b20;
    --green: #4ecdc4;
    --green-dim: #4ecdc420;
    --orange: #ffa726;
    --orange-dim: #ffa72620;
    --purple: #b388ff;
    --purple-dim: #b388ff20;
    --gold: #ffd54f;
    --gold-dim: #ffd54f20;
    --radius: 12px;
    --radius-sm: 8px;
  }}

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: 'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.8;
    -webkit-font-smoothing: antialiased;
  }}

  /* === Layout === */
  .container {{
    max-width: 780px;
    margin: 0 auto;
    padding: 0 24px 100px;
  }}

  /* === Header === */
  .header {{
    text-align: center;
    padding: 60px 0 48px;
    position: relative;
  }}
  .header::after {{
    content: '';
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 60px;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
  }}
  .header .logo {{
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 12px;
  }}
  .header h1 {{
    font-size: 32px;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 8px;
    letter-spacing: -0.5px;
  }}
  .header .date {{
    font-size: 14px;
    color: var(--text-muted);
    font-weight: 400;
  }}

  /* === Sections === */
  .section {{
    margin: 48px 0;
  }}
  .section-header {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border-subtle);
  }}
  .section-icon {{
    width: 36px;
    height: 36px;
    border-radius: var(--radius-sm);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    flex-shrink: 0;
  }}
  .section-title {{
    font-size: 18px;
    font-weight: 600;
    color: var(--text);
    letter-spacing: -0.3px;
  }}

  /* Section theme colors */
  .theme-fire .section-icon {{ background: var(--fire-dim); }}
  .theme-fire .section-header {{ border-bottom-color: var(--fire); border-bottom-width: 2px; }}
  .theme-tools .section-icon {{ background: var(--green-dim); }}
  .theme-tools .section-header {{ border-bottom-color: var(--green); border-bottom-width: 2px; }}
  .theme-papers .section-icon {{ background: var(--accent-glow); }}
  .theme-papers .section-header {{ border-bottom-color: var(--accent); border-bottom-width: 2px; }}
  .theme-money .section-icon {{ background: var(--orange-dim); }}
  .theme-money .section-header {{ border-bottom-color: var(--orange); border-bottom-width: 2px; }}
  .theme-leaders .section-icon {{ background: var(--gold-dim); }}
  .theme-leaders .section-header {{ border-bottom-color: var(--gold); border-bottom-width: 2px; }}
  .theme-people .section-icon {{ background: var(--purple-dim); }}
  .theme-people .section-header {{ border-bottom-color: var(--purple); border-bottom-width: 2px; }}

  /* === Cards === */
  .card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px 24px;
    margin: 16px 0;
    transition: border-color 0.2s, background 0.2s;
  }}
  .card:hover {{
    border-color: var(--accent-dim);
    background: var(--surface-hover);
  }}
  .card h3 {{
    font-size: 16px;
    font-weight: 600;
    color: var(--accent);
    margin-bottom: 12px;
  }}

  /* === Typography === */
  h2 {{ /* handled by section-header */ display: none; }}
  h3 {{
    font-size: 16px;
    font-weight: 600;
    color: var(--accent);
    margin: 28px 0 12px;
  }}

  p {{
    margin: 12px 0;
    color: var(--text-secondary);
    font-size: 15px;
  }}

  strong {{
    color: var(--text);
    font-weight: 600;
  }}

  em {{
    color: var(--text-secondary);
    font-style: italic;
  }}

  /* === Lists === */
  ul, ol {{
    margin: 12px 0;
    padding-left: 20px;
  }}
  li {{
    margin: 8px 0;
    color: var(--text-secondary);
    font-size: 15px;
  }}
  li strong {{
    color: var(--text);
  }}
  li::marker {{
    color: var(--text-muted);
  }}

  /* === Links === */
  a {{
    color: var(--accent);
    text-decoration: none;
    border-bottom: 1px solid transparent;
    transition: border-color 0.2s;
  }}
  a:hover {{
    border-bottom-color: var(--accent);
  }}

  /* === Code === */
  code {{
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 13px;
    font-family: 'JetBrains Mono', 'Cascadia Code', Consolas, monospace;
    color: var(--green);
  }}

  pre {{
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 20px;
    overflow-x: auto;
    margin: 16px 0;
  }}
  pre code {{
    background: none;
    border: none;
    padding: 0;
    color: var(--text-secondary);
  }}

  /* === Blockquotes === */
  blockquote {{
    border-left: 3px solid var(--accent);
    padding: 12px 20px;
    margin: 16px 0;
    background: var(--accent-glow);
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  }}
  blockquote p {{
    color: var(--text);
  }}

  /* === Horizontal Rule === */
  hr {{
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border), transparent);
    margin: 32px 0;
  }}

  /* === Tags === */
  .tag {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 100px;
    font-size: 12px;
    font-weight: 500;
    margin: 2px 4px 2px 0;
  }}
  .tag-fire {{ background: var(--fire-dim); color: var(--fire); }}
  .tag-green {{ background: var(--green-dim); color: var(--green); }}
  .tag-accent {{ background: var(--accent-glow); color: var(--accent); }}

  /* === Footer === */
  .footer {{
    text-align: center;
    margin-top: 80px;
    padding-top: 32px;
    border-top: 1px solid var(--border-subtle);
    color: var(--text-muted);
    font-size: 12px;
    letter-spacing: 0.5px;
  }}

  /* === Responsive === */
  @media (max-width: 600px) {{
    .container {{ padding: 0 16px 60px; }}
    .header {{ padding: 40px 0 32px; }}
    .header h1 {{ font-size: 24px; }}
    .card {{ padding: 16px; }}
    .section {{ margin: 36px 0; }}
  }}

  /* === Scrollbar === */
  ::-webkit-scrollbar {{ width: 6px; }}
  ::-webkit-scrollbar-track {{ background: var(--bg); }}
  ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}
  ::-webkit-scrollbar-thumb:hover {{ background: var(--text-muted); }}
</style>
</head>
<body>
<div class="container">
  {header}
  {content}
  <div class="footer">
    TRENDRADAR &mdash; {timestamp}
  </div>
</div>
</body>
</html>
"""

# Map section emojis/keywords to themes
SECTION_THEMES = [
    ("🔥", "fire", "当前热点方向"),
    ("🛠", "tools", "值得关注的新工具"),
    ("📄", "papers", "今日论文推荐"),
    ("🏆", "leaders", "今日活跃大佬"),
    ("💰", "money", "资金与行业信号"),
    ("👤", "leaders", "大佬动态"),
    ("🌟", "people", "推荐关注的新人物"),
]


def detect_theme(heading_text):
    for emoji, theme, keyword in SECTION_THEMES:
        if emoji in heading_text or keyword in heading_text:
            return theme, emoji
    return "papers", "📋"


def escape_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline_format(text):
    """Apply inline markdown formatting."""
    text = escape_html(text)

    # Links: [text](url)
    text = re.sub(
        r'\[([^\]]+)\]\(([^)]+)\)',
        r'<a href="\2" target="_blank">\1</a>',
        text,
    )
    # Bare URLs
    text = re.sub(
        r'(?<!["\'>=/])(https?://[^\s<>\),]+)',
        r'<a href="\1" target="_blank">\1</a>',
        text,
    )
    # Bold
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
    # Inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

    return text


def md_to_html(md_text):
    """Convert markdown to structured HTML with section cards."""
    lines = md_text.split("\n")
    html_parts = []
    in_list = False
    list_type = "ul"
    in_code = False
    in_blockquote = False
    in_card = False
    in_section = False

    for line in lines:
        stripped = line.strip()

        # Code blocks
        if stripped.startswith("```"):
            if in_code:
                html_parts.append("</code></pre>")
                in_code = False
            else:
                html_parts.append("<pre><code>")
                in_code = True
            continue
        if in_code:
            html_parts.append(escape_html(line) + "\n")
            continue

        # Close list if needed
        if in_list and not stripped.startswith("- ") and not stripped.startswith("* ") and not re.match(r"^\d+\.\s", stripped) and stripped:
            html_parts.append(f"</{list_type}>")
            in_list = False

        # Close blockquote
        if in_blockquote and not stripped.startswith(">"):
            html_parts.append("</blockquote>")
            in_blockquote = False

        # Empty line
        if not stripped:
            continue

        # H1 — skip, handled by header
        if stripped.startswith("# ") and not stripped.startswith("## "):
            continue

        # H2 — section header
        if stripped.startswith("## "):
            # Close previous card and section
            if in_card:
                html_parts.append("</div>")
                in_card = False
            if in_list:
                html_parts.append(f"</{list_type}>")
                in_list = False
            if in_section:
                html_parts.append("</div>")

            title = stripped[3:]
            theme, emoji = detect_theme(title)
            # Remove emoji from title for cleaner display
            clean_title = re.sub(r'^[\U0001F300-\U0001FAD6\U00002702-\U000027B0\U0000FE00-\U0000FE0F\U0001F900-\U0001F9FF]+\s*', '', title)

            html_parts.append(f'<div class="section theme-{theme}">')
            html_parts.append(f'  <div class="section-header">')
            html_parts.append(f'    <div class="section-icon">{emoji}</div>')
            html_parts.append(f'    <div class="section-title">{inline_format(clean_title)}</div>')
            html_parts.append(f'  </div>')
            in_section = True
            continue

        # H3 — card header
        if stripped.startswith("### "):
            if in_card:
                html_parts.append("</div>")
            if in_list:
                html_parts.append(f"</{list_type}>")
                in_list = False
            html_parts.append('<div class="card">')
            html_parts.append(f"<h3>{inline_format(stripped[4:])}</h3>")
            in_card = True
            continue

        # Blockquote
        if stripped.startswith("> "):
            if not in_blockquote:
                html_parts.append("<blockquote>")
                in_blockquote = True
            html_parts.append(f"<p>{inline_format(stripped[2:])}</p>")
            continue

        # Unordered list
        if stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
                list_type = "ul"
            html_parts.append(f"<li>{inline_format(stripped[2:])}</li>")
            continue

        # Ordered list
        if re.match(r"^\d+\.\s", stripped):
            if not in_list:
                html_parts.append("<ol>")
                in_list = True
                list_type = "ol"
            content = re.sub(r"^\d+\.\s", "", stripped)
            html_parts.append(f"<li>{inline_format(content)}</li>")
            continue

        # Horizontal rule
        if stripped in ("---", "***", "___"):
            html_parts.append("<hr>")
            continue

        # Regular paragraph
        html_parts.append(f"<p>{inline_format(stripped)}</p>")

    # Close all open tags
    if in_list:
        html_parts.append(f"</{list_type}>")
    if in_code:
        html_parts.append("</code></pre>")
    if in_blockquote:
        html_parts.append("</blockquote>")
    if in_card:
        html_parts.append("</div>")
    if in_section:
        html_parts.append("</div>")

    return "\n".join(html_parts)


def render(md_path, output_path=None):
    """Render a markdown file to styled HTML."""
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Extract date
    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", md_text[:200])
    date_str = date_match.group(1) if date_match else datetime.now().strftime("%Y-%m-%d")

    # Format date nicely
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        weekdays_cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        date_display = f"{dt.year} 年 {dt.month} 月 {dt.day} 日 {weekdays_cn[dt.weekday()]}"
    except ValueError:
        date_display = date_str

    header_html = f"""
    <div class="header">
      <div class="logo">TrendRadar</div>
      <h1>Daily Intelligence Briefing</h1>
      <div class="date">{date_display}</div>
    </div>
    """

    content_html = md_to_html(md_text)

    html = HTML_TEMPLATE.format(
        title=f"TrendRadar - {date_str}",
        header=header_html,
        content=content_html,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    if output_path is None:
        base = os.path.splitext(os.path.basename(md_path))[0]
        output_path = os.path.join(OUTPUT_DIR, f"{base}.html")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"HTML rendered to {output_path}")
    return output_path


def main():
    if len(sys.argv) > 1:
        md_path = sys.argv[1]
    else:
        today = datetime.now().strftime("%Y-%m-%d")
        md_path = os.path.join(OUTPUT_DIR, f"briefing-{today}.md")

    if not os.path.exists(md_path):
        print(f"File not found: {md_path}")
        print("Usage: python render.py [path/to/briefing.md]")
        sys.exit(1)

    output_path = render(md_path)

    import webbrowser
    webbrowser.open(output_path)


if __name__ == "__main__":
    main()
