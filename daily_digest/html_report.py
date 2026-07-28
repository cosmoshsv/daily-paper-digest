import datetime
import html

VERDICT_META = {
    "must_read": ("Must-read", "must"),
    "worth_a_skim": ("Recommended", "rec"),
    "radar": ("On radar", "radar"),
}

_CSS = """
:root {
  --paper: #f4f1e8; --ink: #16150f; --muted: #6b6559; --rule: #cfc7b4;
  --must: #9c2b1b; --rec: #1f5b7a;
}
@media (prefers-color-scheme: dark) {
  :root {
    --paper: #14130f; --ink: #ece7db; --muted: #918a7c; --rule: #35322a;
    --must: #e0705c; --rec: #6fb0d4;
  }
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: var(--paper); color: var(--ink);
  font-family: Georgia, 'Iowan Old Style', 'Times New Roman', serif;
  padding: 1.5rem 1.75rem 5rem; -webkit-font-smoothing: antialiased;
}
.sheet { max-width: 1180px; margin: 0 auto; }

.meta-font {
  font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace;
  text-transform: uppercase; letter-spacing: 0.09em;
}

/* ---- top bar ---- */
.topbar {
  display: flex; justify-content: space-between; align-items: center;
  font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace;
  text-transform: uppercase; letter-spacing: 0.1em;
  font-size: 0.62rem; color: var(--muted);
  padding-bottom: 0.75rem; border-bottom: 1px solid var(--rule);
}
.topbar a { color: inherit; text-decoration: none; }
.topbar a:hover { color: var(--ink); }

/* ---- masthead ---- */
.masthead { text-align: center; padding: 2.4rem 0 1.4rem; }
.masthead h1 {
  font-family: 'Didot', 'Bodoni MT', 'Playfair Display', Georgia, serif;
  font-size: clamp(2.6rem, 7vw, 4.4rem); font-weight: 400;
  letter-spacing: -0.015em; line-height: 1;
}
.masthead .tagline {
  font-style: italic; color: var(--muted); font-size: 0.95rem; margin-top: 0.75rem;
}

/* ---- filter bar ---- */
.filters {
  display: flex; justify-content: space-between; align-items: center;
  flex-wrap: wrap; gap: 0.75rem;
  border-top: 3px double var(--rule); border-bottom: 1px solid var(--rule);
  padding: 0.75rem 0; margin-bottom: 2.25rem;
}
.fgroup { display: flex; align-items: center; gap: 0.5rem; }
.fgroup > span { font-size: 0.6rem; color: var(--muted); }
.pill {
  font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace;
  text-transform: uppercase; letter-spacing: 0.07em; font-size: 0.58rem;
  padding: 0.2rem 0.5rem; border: 1px solid var(--rule); border-radius: 2px;
  background: none; color: var(--muted); cursor: pointer;
}
.pill:hover { color: var(--ink); border-color: var(--ink); }
.pill[aria-pressed="true"] { background: var(--ink); color: var(--paper); border-color: var(--ink); }

/* ---- bylines & tags ---- */
.byline {
  font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace;
  text-transform: uppercase; letter-spacing: 0.08em;
  font-size: 0.58rem; color: var(--muted); line-height: 1.7;
  margin-bottom: 0.7rem; display: flex; flex-wrap: wrap; gap: 0.4rem;
  align-items: center;
}
.byline .sep { opacity: 0.45; }
.tag { color: var(--ink); }
.sig-must { color: var(--must); font-weight: 700; }
.sig-rec { color: var(--rec); font-weight: 700; }
.sig-radar { color: var(--muted); }
.byline a { color: inherit; text-decoration: none; border-bottom: 1px solid var(--rule); }
.byline a:hover { color: var(--ink); }

/* ---- articles ---- */
h2.head {
  font-weight: 400; line-height: 1.28; letter-spacing: -0.01em;
  margin-bottom: 0.75rem;
}
h2.head a { color: inherit; text-decoration: none; }
h2.head a:hover { text-decoration: underline; text-underline-offset: 3px; }
.art p { font-size: 0.9rem; line-height: 1.78; text-align: justify; hyphens: auto; }
.art .kicker {
  margin-top: 0.9rem; color: var(--muted); font-style: italic;
  font-size: 0.84rem; line-height: 1.65; text-align: left;
}
.dropcap::first-letter {
  float: left; font-size: 4.4em; line-height: 0.84; padding: 0.04em 0.09em 0 0;
  font-family: 'Didot', 'Bodoni MT', Georgia, serif;
}

/* ---- lead ---- */
.lead { border-bottom: 3px double var(--rule); padding-bottom: 2.5rem; margin-bottom: 2.5rem; }
.lead h2.head { font-size: clamp(1.7rem, 3.6vw, 2.6rem); margin-bottom: 1.1rem; }
.lead .cols { column-count: 2; column-gap: 2.75rem; column-rule: 1px solid var(--rule); }
@media (max-width: 700px) { .lead .cols { column-count: 1; } }

/* ---- column flow ---- */
.flow { column-count: 3; column-gap: 2.5rem; column-rule: 1px solid var(--rule); }
@media (max-width: 980px) { .flow { column-count: 2; } }
@media (max-width: 640px) { .flow { column-count: 1; } }
.flow .art {
  break-inside: avoid; -webkit-column-break-inside: avoid;
  padding-bottom: 1.9rem; margin-bottom: 1.9rem; border-bottom: 1px solid var(--rule);
}
.flow h2.head { font-size: 1.18rem; }
.art[hidden] { display: none; }

.empty { text-align: center; font-style: italic; color: var(--muted); padding: 3rem 0; }
.nomatch { text-align: center; font-style: italic; color: var(--muted); padding: 2rem 0; }
footer {
  border-top: 3px double var(--rule); margin-top: 2rem; padding-top: 0.75rem;
  font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace;
  text-transform: uppercase; letter-spacing: 0.09em;
  font-size: 0.58rem; color: var(--muted); text-align: center;
}
"""

_JS = """
(function () {
  var state = { source: 'all', signal: 'all' };
  var arts = Array.prototype.slice.call(document.querySelectorAll('.flow .art'));
  var nomatch = document.getElementById('nomatch');

  function apply() {
    var shown = 0;
    arts.forEach(function (a) {
      var ok = (state.source === 'all' || a.dataset.source === state.source) &&
               (state.signal === 'all' || a.dataset.signal === state.signal);
      a.hidden = !ok;
      if (ok) shown++;
    });
    if (nomatch) nomatch.hidden = shown > 0;
  }

  document.querySelectorAll('.pill').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var group = btn.dataset.group;
      state[group] = btn.dataset.value;
      document.querySelectorAll('.pill[data-group="' + group + '"]').forEach(function (b) {
        b.setAttribute('aria-pressed', String(b === btn));
      });
      apply();
    });
  });
})();
"""


def _esc(text):
    return html.escape(str(text))


def _first_author(authors):
    return authors[0] if authors else "Unknown"


def _signal_key(verdict):
    return VERDICT_META.get(verdict, VERDICT_META["radar"])[1]


def _byline(paper):
    label, cls = VERDICT_META.get(paper["verdict"], VERDICT_META["radar"])
    bits = [
        f'<span>By {_esc(_first_author(paper["authors"]))}</span>',
        '<span class="sep">·</span>',
        f'<span class="sig-{cls}">{_esc(label)}</span>',
    ]
    for tag in paper["topics"][:2]:
        bits.append('<span class="sep">·</span>')
        bits.append(f'<span class="tag">{_esc(tag)}</span>')
    bits.append('<span class="sep">·</span>')
    bits.append(f'<span>{_esc(paper["source"])}</span>')
    bits.append('<span class="sep">·</span>')
    bits.append(f'<a href="{_esc(paper["url"])}">Read</a>')
    return '<div class="byline">' + "".join(bits) + "</div>"


def _article(paper, lead=False):
    body = paper.get("body") or paper["tldr"]
    text = (
        f'<div class="cols"><p class="dropcap">{_esc(body)}</p>'
        f'<p class="kicker">Why it matters: {_esc(paper["why_it_matters"])}</p></div>'
        if lead
        else f'<p class="dropcap">{_esc(body)}</p>'
        f'<p class="kicker">Why it matters: {_esc(paper["why_it_matters"])}</p>'
    )
    return f"""<article class="art"
  data-source="{_esc(paper["source"].lower())}"
  data-signal="{_signal_key(paper["verdict"])}">
  {_byline(paper)}
  <h2 class="head"><a href="{_esc(paper["url"])}">{_esc(paper["title"])}</a></h2>
  {text}
</article>"""


def _pills(group, options):
    out = []
    for i, (value, label) in enumerate(options):
        pressed = "true" if i == 0 else "false"
        out.append(
            f'<button class="pill" data-group="{group}" data-value="{_esc(value)}" '
            f'aria-pressed="{pressed}">{_esc(label)}</button>'
        )
    return "".join(out)


def build_html(date_str, papers, profile):
    masthead = profile.get("masthead") or "The Daily Read"
    tagline = profile.get("tagline") or "Papers Worth Your Time"

    try:
        d = datetime.date.fromisoformat(date_str)
        pretty_date = f"{d:%A, %B} {d.day}, {d.year}".upper()
    except (ValueError, TypeError):
        pretty_date = str(date_str).upper()

    if not papers:
        content = '<p class="empty">No dispatches today — nothing cleared the bar.</p>'
        filters = ""
    else:
        lead, rest = papers[0], papers[1:]
        flow = "\n".join(_article(p) for p in rest)
        content = (
            f'<section class="lead">{_article(lead, lead=True)}</section>'
            f'<section class="flow">{flow}</section>'
            '<p class="nomatch" id="nomatch" hidden>Nothing matches that filter.</p>'
            if rest
            else f'<section class="lead">{_article(lead, lead=True)}</section>'
        )
        sources = sorted({p["source"] for p in papers})
        source_opts = [("all", "All")] + [(s.lower(), s) for s in sources]
        signal_opts = [
            ("all", "All"),
            ("must", "Must-read"),
            ("rec", "Recommended"),
        ]
        filters = f"""
  <nav class="filters">
    <div class="fgroup"><span>Source:</span>{_pills("source", source_opts)}</div>
    <div class="fgroup"><span>Signal:</span>{_pills("signal", signal_opts)}</div>
  </nav>"""

    count = len(papers)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(masthead)} — {_esc(date_str)}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="sheet">
  <div class="topbar">
    <span>Ranked against profile.yaml</span>
    <span>{_esc(pretty_date)}</span>
    <span>{count} {"story" if count == 1 else "stories"}</span>
  </div>
  <header class="masthead">
    <h1>{_esc(masthead)}</h1>
    <p class="tagline">{_esc(tagline)}</p>
  </header>{filters}
  {content}
  <footer>Assembled from arXiv &middot; Ranked for you</footer>
</div>
<script>{_JS}</script>
</body>
</html>
"""
