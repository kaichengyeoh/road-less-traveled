#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — Static site generator for 少有人走的路
Reads 49 .md files from ../chapters/, outputs site/chapters/*.html + site/index.html
"""

import os
import re
import html as html_lib
from pathlib import Path

# ─────────────────────────────────────────────
# Chapter catalogue  (global order 1–49)
# Each entry: (md_slug, section_number, display_section_title, display_chapter_number_label)
# ─────────────────────────────────────────────

SECTIONS = [
    {
        "label": "SECTION I",
        "title": "紀律",
        "en": "Discipline",
        "desc": "用紀律面對問題，是解決人生苦難的基本工具。",
        "slugs": [
            "01-problems-and-pain",
            "02-delaying-gratification",
            "03-the-sins-of-the-father",
            "04-problem-solving-and-time",
            "05-responsibility",
            "06-neuroses-and-character-disorders",
            "07-escape-from-freedom",
            "08-dedication-to-reality",
            "09-transference-the-outdated-map",
            "10-openness-to-challenge",
            "11-withholding-truth",
            "12-balancing",
            "13-the-healthiness-of-depression",
            "14-renunciation-and-rebirth",
        ],
    },
    {
        "label": "SECTION II",
        "title": "愛",
        "en": "Love",
        "desc": "愛不是感覺，是滋養靈性成長的意志行動。",
        "slugs": [
            "01-falling-in-love",
            "02-the-myth-of-romantic-love",
            "03-more-about-ego-boundaries",
            "04-dependency",
            "05-love-is-not-a-feeling",
            "06-the-work-of-attention",
            "07-the-risk-of-loss",
            "08-the-risk-of-independence",
            "09-the-risk-of-commitment",
            "10-the-risk-of-confrontation",
            "11-love-is-disciplined",
            "12-love-is-separateness",
            "13-love-and-psychotherapy",
            "14-the-mystery-of-love",
        ],
    },
    {
        "label": "SECTION III",
        "title": "成長與宗教",
        "en": "Growth and Religion",
        "desc": "每個人都有世界觀，而世界觀就是你的宗教。",
        "slugs": [
            "15-world-views-and-religion",
            "16-the-religion-of-science",
            "17-the-case-of-kathy",
            "18-the-case-of-marcia",
            "19-the-case-of-theodore",
            "20-the-baby-and-the-bathwater",
            "21-scientific-tunnel-vision",
        ],
    },
    {
        "label": "SECTION IV",
        "title": "恩典",
        "en": "Grace",
        "desc": "有一股超越意識的力量，持續地推動我們走向成長。",
        "slugs": [
            "22-the-miracle-of-health",
            "23-the-miracle-of-the-unconscious",
            "24-the-miracle-of-serendipity",
            "25-the-definition-of-grace",
            "26-the-miracle-of-evolution",
            "27-the-alpha-and-omega",
            "28-entropy-and-original-sin",
            "29-the-problem-of-evil",
            "30-the-evolution-of-consciousness",
            "31-the-nature-of-power",
            "32-grace-and-mental-illness-the-myth-of-orestes",
            "33-resistance-to-grace",
            "34-the-welcoming-of-grace",
            "35-afterword",
        ],
    },
]

# Build a flat global list: [(slug, section_idx, local_pos_in_section), ...]
GLOBAL_ORDER = []
for si, sec in enumerate(SECTIONS):
    for li, slug in enumerate(sec["slugs"]):
        GLOBAL_ORDER.append((slug, si, li))

TOTAL = len(GLOBAL_ORDER)  # 49


# ─────────────────────────────────────────────
# Markdown → HTML helpers
# ─────────────────────────────────────────────

def esc(s):
    """HTML-escape a string."""
    return html_lib.escape(s, quote=False)


def inline_md(text):
    """Convert **bold** and *italic* to HTML spans."""
    # Bold first
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Then italic (single *)
    text = re.sub(r'\*([^*\n]+?)\*', r'<em>\1</em>', text)
    return text


def lines_to_html(lines, section_class=""):
    """
    Convert a list of raw text lines (within a section) to HTML.
    Handles: blockquotes, bullet lists, paragraphs.
    Returns raw HTML string.
    """
    html_parts = []
    i = 0
    in_ul = False
    in_bq = False
    bq_lines = []

    def flush_bq():
        nonlocal bq_lines
        if not bq_lines:
            return ""
        # Each pair of consecutive bq lines = (EN, ZH)
        out = ""
        j = 0
        while j < len(bq_lines):
            line = bq_lines[j].strip()
            # Skip label lines like **一句話帶走：**...
            if line.startswith("**") and "一句話帶走" in line:
                j += 1
                continue
            # Pair: EN + ZH
            en_line = line
            zh_line = bq_lines[j + 1].strip() if (j + 1) < len(bq_lines) else ""
            out += '<blockquote>\n'
            out += f'  <p class="quote-en">{inline_md(esc(en_line))}</p>\n'
            if zh_line:
                out += f'  <p class="quote-zh">{inline_md(esc(zh_line))}</p>\n'
                j += 2
            else:
                j += 1
            out += '</blockquote>\n'
        bq_lines = []
        return out

    def flush_ul():
        nonlocal html_parts, in_ul
        if in_ul:
            html_parts.append("</ul>")
            in_ul = False

    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()

        # Blockquote line
        if stripped.startswith(">"):
            if in_ul:
                flush_ul()
            content = stripped[1:].strip()
            # Skip empty bq lines
            if content:
                bq_lines.append(content)
            i += 1
            continue

        # If we were collecting bq lines and this line is not bq, flush
        if bq_lines:
            html_parts.append(flush_bq())

        # Empty line
        if not stripped:
            if in_ul:
                flush_ul()
            i += 1
            continue

        # Bullet list item
        if stripped.startswith("- "):
            if not in_ul:
                html_parts.append("<ul>")
                in_ul = True
            content = stripped[2:].strip()
            html_parts.append(f"  <li>{inline_md(esc(content))}</li>")
            i += 1
            continue

        # Numbered list item (reflection questions)
        m = re.match(r'^(\d+)\.\s+(.*)', stripped)
        if m:
            if in_ul:
                flush_ul()
            # We handle numbered lists as <ol> - but let's just use <li> wrapped in ol
            # We'll detect if we're in an ol by checking the last element
            if not html_parts or not html_parts[-1].startswith("<ol"):
                html_parts.append("<ol>")
            content = m.group(2).strip()
            html_parts.append(f"  <li>{inline_md(esc(content))}</li>")
            # Peek: is next line also numbered?
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and re.match(r'^\d+\.\s+', lines[j].strip()):
                i += 1
                continue
            else:
                # Close ol
                html_parts.append("</ol>")
                i += 1
                continue

        # Normal paragraph
        if in_ul:
            flush_ul()
        html_parts.append(f"<p>{inline_md(esc(stripped))}</p>")
        i += 1

    # Flush remaining
    if bq_lines:
        html_parts.append(flush_bq())
    if in_ul:
        flush_ul()
    # Close any unclosed ol
    if html_parts and html_parts[-1].startswith("  <li>"):
        html_parts.append("</ol>")

    return "\n".join(html_parts)


def parse_chapter(md_text):
    """
    Parse a chapter .md file into structured dict:
    {
      title, original_title, takeaway,
      sections: [{"heading": str, "lines": [str], "id": str}, ...]
    }
    """
    lines = md_text.splitlines()
    result = {
        "title": "",
        "original_title": "",
        "takeaway": "",
        "sections": [],
    }

    current_section = None
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # H1 title
        if stripped.startswith("# ") and not stripped.startswith("## "):
            result["title"] = stripped[2:].strip()
            i += 1
            continue

        # Original title (*原文標題：...*  or  *原文標題：..*)
        m = re.match(r'^\*原文標題[：:]\s*(.+?)\*$', stripped)
        if m:
            result["original_title"] = m.group(1).strip()
            i += 1
            continue

        # Takeaway blockquote (first > line that has 一句話帶走)
        if stripped.startswith(">") and "一句話帶走" in stripped:
            # Extract content after the colon
            content = stripped.lstrip(">").strip()
            # Remove leading **一句話帶走：** markup
            content = re.sub(r'^\*\*一句話帶走[：:]\*\*\s*', '', content)
            result["takeaway"] = content.strip()
            i += 1
            continue

        # H2 section heading
        if stripped.startswith("## "):
            heading = stripped[3:].strip()
            # Determine section id/class
            sid = "section-" + re.sub(r'\s+', '-', heading)
            if "核心概念" in heading:
                sid = "section-core"
            elif "關鍵洞" in heading:
                sid = "section-insights"
            elif "書中金句" in heading:
                sid = "section-quotes"
            elif "反思" in heading:
                sid = "section-reflection"
            current_section = {"heading": heading, "lines": [], "id": sid}
            result["sections"].append(current_section)
            i += 1
            continue

        # Content line
        if current_section is not None:
            current_section["lines"].append(line)

        i += 1

    return result


# ─────────────────────────────────────────────
# HTML templates
# ─────────────────────────────────────────────

HTML_HEAD = """\
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{page_title} — 少有人走的路</title>
  <link rel="stylesheet" href="{css_path}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@300;400;500;600&family=Noto+Sans+TC:wght@300;400;500&display=swap" rel="stylesheet">
</head>
<body>
"""

HTML_HEADER = """\
<header class="site-header">
  <div class="logo"><strong>少有人走的路</strong> &nbsp;·&nbsp; M. Scott Peck</div>
  <a href="{home_path}" class="nav-home">← 目錄</a>
</header>
"""

HTML_FOOTER = """\
<footer class="site-footer">
  少有人走的路 &nbsp;·&nbsp; M. Scott Peck &nbsp;·&nbsp; 學習筆記
</footer>
</body>
</html>
"""


def build_chapter_html(slug, global_idx, md_text):
    """Generate full HTML for a single chapter page."""
    sec_idx = GLOBAL_ORDER[global_idx][1]
    sec = SECTIONS[sec_idx]
    local_idx = GLOBAL_ORDER[global_idx][2]

    chapter = parse_chapter(md_text)

    # Progress
    progress_pct = round((global_idx + 1) / TOTAL * 100)

    # Prev / Next
    prev_slug = GLOBAL_ORDER[global_idx - 1][0] if global_idx > 0 else None
    next_slug = GLOBAL_ORDER[global_idx + 1][0] if global_idx < TOTAL - 1 else None

    def get_title_for(idx):
        s = GLOBAL_ORDER[idx][0]
        md_path = CHAPTERS_DIR / f"{s}.md"
        if md_path.exists():
            for ln in md_path.read_text(encoding="utf-8").splitlines():
                if ln.startswith("# ") and not ln.startswith("## "):
                    return ln[2:].strip()
        return s

    prev_title = get_title_for(global_idx - 1) if prev_slug else ""
    next_title = get_title_for(global_idx + 1) if next_slug else ""

    # Chapter number label
    chap_num = f"{sec['label']} &nbsp;·&nbsp; {local_idx + 1:02d} / {len(sec['slugs']):02d}"

    # Build sections HTML
    sections_html = ""
    for section in chapter["sections"]:
        sid = section["id"]
        heading_esc = esc(section["heading"])
        body_html = lines_to_html(section["lines"], sid)
        sections_html += f"""
<div class="chapter-section {sid}">
  <h2>{heading_esc}</h2>
  {body_html}
</div>"""

    # Prev/next nav
    nav_prev = ""
    nav_next = ""
    if prev_slug:
        nav_prev = f"""<a class="nav-btn nav-prev" href="{prev_slug}.html">
  <span class="nav-dir">← 上一節</span>
  <span class="nav-title">{esc(prev_title)}</span>
</a>"""
    else:
        nav_prev = '<div class="nav-spacer"></div>'

    if next_slug:
        nav_next = f"""<a class="nav-btn nav-next" href="{next_slug}.html">
  <span class="nav-dir">下一節 →</span>
  <span class="nav-title">{esc(next_title)}</span>
</a>"""
    else:
        nav_next = '<div class="nav-spacer"></div>'

    takeaway_html = ""
    if chapter["takeaway"]:
        takeaway_html = f"""<div class="takeaway-banner">
  <strong>一句話帶走</strong>{esc(chapter["takeaway"])}
</div>"""

    original_html = ""
    if chapter["original_title"]:
        original_html = f'<p class="chapter-original">{esc(chapter["original_title"])}</p>'

    html = HTML_HEAD.format(
        page_title=esc(chapter["title"]),
        css_path="../style.css"
    )
    html += HTML_HEADER.format(home_path="../index.html")
    html += f'<div class="progress-bar" style="width:{progress_pct}%"></div>\n'
    html += '<main class="chapter-wrap">\n'
    html += f'''<div class="chapter-meta">
  <p class="chapter-num">{chap_num}</p>
  <h1>{esc(chapter["title"])}</h1>
  {original_html}
  {takeaway_html}
</div>
'''
    html += sections_html
    html += f'''
<nav class="chapter-nav">
  {nav_prev}
  {nav_next}
</nav>
<p class="chapter-progress">{global_idx + 1} / {TOTAL}</p>
'''
    html += '</main>\n'
    html += HTML_FOOTER
    return html


def build_index_html():
    """Generate the index page with 4 section groups and chapter cards."""
    cards_by_section = []
    for si, sec in enumerate(SECTIONS):
        cards_html = ""
        for li, slug in enumerate(sec["slugs"]):
            global_idx = sum(len(SECTIONS[x]["slugs"]) for x in range(si)) + li
            md_path = CHAPTERS_DIR / f"{slug}.md"
            title = slug
            takeaway = ""
            original_title = ""
            if md_path.exists():
                text = md_path.read_text(encoding="utf-8")
                for ln in text.splitlines():
                    stripped = ln.strip()
                    if stripped.startswith("# ") and not stripped.startswith("## "):
                        title = stripped[2:].strip()
                    m = re.match(r'^\*原文標題[：:]\s*(.+?)\*$', stripped)
                    if m:
                        original_title = m.group(1).strip()
                    if stripped.startswith(">") and "一句話帶走" in stripped:
                        content = stripped.lstrip(">").strip()
                        content = re.sub(r'^\*\*一句話帶走[：:]\*\*\s*', '', content)
                        takeaway = content.strip()

            num_label = f"{si + 1}-{li + 1:02d}"
            cards_html += f"""<a class="chapter-card" href="chapters/{slug}.html">
  <span class="card-num">{num_label}</span>
  <span class="card-title">{esc(title)}</span>
  <span class="card-subtitle">{esc(original_title)}</span>
  <span class="card-takeaway">{esc(takeaway)}</span>
</a>
"""
        cards_by_section.append(cards_html)

    # Build section groups
    groups_html = ""
    for si, sec in enumerate(SECTIONS):
        groups_html += f"""
<section class="section-group">
  <p class="section-label">{esc(sec["label"])}</p>
  <h2 class="section-title">{esc(sec["title"])} <span style="color:var(--text-muted);font-weight:300;font-size:0.85em">— {esc(sec["en"])}</span></h2>
  <p class="section-desc">{esc(sec["desc"])}</p>
  <div class="card-grid">
    {cards_by_section[si]}
  </div>
</section>
"""

    html = HTML_HEAD.format(
        page_title="目錄",
        css_path="style.css"
    )
    html += HTML_HEADER.format(home_path="index.html")
    html += """<main>
<div class="index-hero">
  <h1><em>少有人走的路</em></h1>
  <p class="subtitle">The Road Less Traveled &nbsp;·&nbsp; M. Scott Peck &nbsp;·&nbsp; 學習筆記</p>
  <div class="divider"></div>
  <p style="font-family:var(--font-sans);font-size:0.85rem;color:var(--text-muted);max-width:420px;margin:0 auto;line-height:1.8;">
    49 個子節 &nbsp;·&nbsp; 4 個主題 &nbsp;·&nbsp; 一條少有人走的路
  </p>
</div>
"""
    html += groups_html
    html += "</main>\n"
    html += HTML_FOOTER
    return html


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # Paths
    SCRIPT_DIR   = Path(__file__).parent
    SITE_DIR     = SCRIPT_DIR
    CHAPTERS_DIR = SCRIPT_DIR.parent / "chapters"
    OUT_DIR      = SITE_DIR / "chapters"
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Source:  {CHAPTERS_DIR}")
    print(f"Output:  {OUT_DIR}")
    print()

    generated = 0
    missing = []

    for global_idx, (slug, si, li) in enumerate(GLOBAL_ORDER):
        md_path = CHAPTERS_DIR / f"{slug}.md"
        if not md_path.exists():
            print(f"  [MISSING] {slug}.md")
            missing.append(slug)
            continue

        md_text = md_path.read_text(encoding="utf-8")
        out_path = OUT_DIR / f"{slug}.html"
        html_content = build_chapter_html(slug, global_idx, md_text)
        out_path.write_text(html_content, encoding="utf-8")
        print(f"  [{global_idx + 1:02d}/{TOTAL}] {slug}.html")
        generated += 1

    # Index
    index_path = SITE_DIR / "index.html"
    index_html = build_index_html()
    index_path.write_text(index_html, encoding="utf-8")
    print(f"\n  [IDX] index.html")

    print(f"\n✓ Generated {generated} chapter pages + index.html")
    if missing:
        print(f"✗ Missing: {missing}")
