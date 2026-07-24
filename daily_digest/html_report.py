import html

from .report import format_authors

VERDICT_META = {
    "must_read": ("Must read", "must"),
    "worth_a_skim": ("Worth a skim", "skim"),
    "radar": ("On your radar", "radar"),
}

_CSS = """
:root {
  --bg: #faf9f6; --card: #ffffff; --text: #1c1c1e; --muted: #6e6e73;
  --border: #e6e4de; --accent: #b45309;
  --must: #b91c1c; --must-bg: #fef2f2;
  --skim: #b45309; --skim-bg: #fffbeb;
  --radar: #52525b; --radar-bg: #f4f4f5;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #101014; --card: #1a1a20; --text: #ececf1; --muted: #9a9aa3;
    --border: #2a2a32; --accent: #f59e0b;
    --must: #f87171; --must-bg: #2c1515;
    --skim: #fbbf24; --skim-bg: #2a2110;
    --radar: #a1a1aa; --radar-bg: #232329;
  }
}
* { box-sizing: border-box; margin: 0; }
body {
  background: var(--bg); color: var(--text);
  font: 16px/1.6 Georgia, 'Times New Roman', serif;
  padding: 2.5rem 1rem 4rem;
}
.wrap { max-width: 720px; margin: 0 auto; }
header { margin-bottom: 2rem; }
header h1 { font-size: 1.9rem; font-weight: 600; letter-spacing: -0.01em; }
header .date { color: var(--muted); font-size: 0.95rem; margin-top: 0.25rem; }
header .profile-note { color: var(--muted); font-size: 0.85rem; margin-top: 0.5rem;
  font-family: -apple-system, 'Segoe UI', system-ui, sans-serif; }
.card {
  background: var(--card); border: 1px solid var(--border); border-radius: 12px;
  padding: 1.4rem 1.5rem; margin-bottom: 1.25rem;
}
.card .meta {
  display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap;
  font-family: -apple-system, 'Segoe UI', system-ui, sans-serif;
  font-size: 0.78rem; margin-bottom: 0.6rem;
}
.badge { padding: 0.15rem 0.55rem; border-radius: 999px; font-weight: 600; }
.badge.must  { color: var(--must);  background: var(--must-bg); }
.badge.skim  { color: var(--skim);  background: var(--skim-bg); }
.badge.radar { color: var(--radar); background: var(--radar-bg); }
.score { color: var(--muted); font-weight: 600; }
.score b { color: var(--accent); font-size: 0.95rem; }
.card h2 { font-size: 1.2rem; line-height: 1.35; font-weight: 600; }
.card h2 a { color: inherit; text-decoration: none; }
.card h2 a:hover { text-decoration: underline; }
.authors { color: var(--muted); font-size: 0.85rem; margin-top: 0.25rem; font-style: italic; }
.tldr { margin-top: 0.75rem; }
.why { margin-top: 0.6rem; color: var(--muted); font-size: 0.95rem; }
.why b { color: var(--text); }
.tags { margin-top: 0.8rem; display: flex; gap: 0.4rem; flex-wrap: wrap;
  font-family: -apple-system, 'Segoe UI', system-ui, sans-serif; }
.tag { font-size: 0.72rem; color: var(--muted); border: 1px solid var(--border);
  border-radius: 6px; padding: 0.1rem 0.45rem; }
.links { margin-top: 0.8rem; font-size: 0.82rem;
  font-family: -apple-system, 'Segoe UI', system-ui, sans-serif; }
.links a { color: var(--accent); text-decoration: none; margin-right: 0.9rem; }
.links a:hover { text-decoration: underline; }
.empty { color: var(--muted); font-style: italic; padding: 2rem 0; }
footer { color: var(--muted); font-size: 0.78rem; margin-top: 2.5rem;
  font-family: -apple-system, 'Segoe UI', system-ui, sans-serif; }
"""


def _pdf_url(paper):
    return paper["url"].replace("/abs/", "/pdf/")


def _card(paper):
    label, cls = VERDICT_META.get(paper["verdict"], (paper["verdict"], "radar"))
    tags = "".join(
        f'<span class="tag">{html.escape(t)}</span>' for t in paper["topics"]
    )
    return f"""
<article class="card">
  <div class="meta">
    <span class="badge {cls}">{html.escape(label)}</span>
    <span class="score">worth <b>{paper["worth_score"]}/10</b></span>
  </div>
  <h2><a href="{html.escape(paper["url"])}">{html.escape(paper["title"])}</a></h2>
  <div class="authors">{html.escape(format_authors(paper["authors"]))}</div>
  <p class="tldr">{html.escape(paper["tldr"])}</p>
  <p class="why"><b>Why it matters:</b> {html.escape(paper["why_it_matters"])}</p>
  <div class="tags">{tags}</div>
  <div class="links">
    <a href="{html.escape(paper["url"])}">abstract</a>
    <a href="{html.escape(_pdf_url(paper))}">pdf</a>
  </div>
</article>"""


def build_html(date_str, papers, profile):
    topic_names = ", ".join(t["name"] for t in profile["topics"])
    if papers:
        body = "\n".join(_card(p) for p in papers)
    else:
        body = '<p class="empty">Nothing cleared the bar today — enjoy the free time.</p>'
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Daily Paper Digest — {html.escape(date_str)}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Daily Paper Digest</h1>
    <div class="date">{html.escape(date_str)}</div>
    <div class="profile-note">Ranked for: {html.escape(topic_names)}</div>
  </header>
  {body}
  <footer>Generated from arXiv, ranked against profile.yaml.</footer>
</div>
</body>
</html>
"""
