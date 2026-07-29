import datetime
import os
import re

import anthropic

from .arxiv_client import search_papers
from .config import CLAUDE_MODEL, MAX_TOKENS, REPORTS_DIR, TOPIC_ARXIV_MAX_RESULTS
from .html_report import build_html
from .report import build_markdown
from .summarizer import VERDICTS, parse_json_response

WEB_SEARCH_TOOL = {"type": "web_search_20260209", "name": "web_search"}

BRIEFING_SCHEMA = {
    "type": "object",
    "properties": {
        "takeaway": {
            "type": "string",
            "description": "2-3 sentences synthesizing where this topic stands right now.",
        },
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "url": {"type": "string"},
                    "source": {
                        "type": "string",
                        "enum": ["arXiv", "Web", "X"],
                        "description": "arXiv for papers, Web for articles/blogs/news, X for Twitter/X chatter.",
                    },
                    "author": {
                        "type": "string",
                        "description": "First author, publication, or handle. 'Unknown' if unclear.",
                    },
                    "body": {
                        "type": "string",
                        "description": (
                            "3-5 sentences of newspaper-style prose. Plain declarative "
                            "sentences, no bullets, no markdown, no hype."
                        ),
                    },
                    "why_it_matters": {
                        "type": "string",
                        "description": "One sentence on why this matters for someone learning this topic.",
                    },
                    "worth_score": {"type": "integer", "description": "1-10 relevance to the topic."},
                    "verdict": {"type": "string", "enum": VERDICTS},
                    "topics": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "title",
                    "url",
                    "source",
                    "author",
                    "body",
                    "why_it_matters",
                    "worth_score",
                    "verdict",
                    "topics",
                ],
                "additionalProperties": False,
            },
        },
    },
    "required": ["takeaway", "items"],
    "additionalProperties": False,
}


def _format_arxiv_hits(papers):
    if not papers:
        return "(no matching arXiv papers found)"
    lines = []
    for p in papers:
        date = p["published"][:10]
        excerpt = p["summary"][:300].rstrip() + ("..." if len(p["summary"]) > 300 else "")
        lines.append(f"- **{p['title']}** ({p['id']}, {date}) — {excerpt}\n  {p['url']}")
    return "\n".join(lines)


def _slugify(topic):
    return re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")[:50] or "topic"


def _research(client, topic, arxiv_block):
    """Pass 1: gather material with the web_search tool. Returns free text."""
    prompt = (
        f'Research the topic: "{topic}"\n\n'
        "Here are recent matching arXiv papers (may be incomplete or only "
        "partially relevant - use judgment about what to include):\n\n"
        f"{arxiv_block}\n\n"
        "Using the web_search tool, also look for:\n"
        "1. Recent news, blog posts, or technical discussion about this topic "
        "(prioritize the last few weeks).\n"
        "2. Any notable recent discussion of this topic on Twitter/X - search "
        "for it specifically (e.g. site:twitter.com or site:x.com). This is "
        "NOT true trending-topic data (no X API access) - it's just whatever "
        "is indexed on the open web. Note that caveat rather than implying "
        "it's live trend data.\n\n"
        "Then write up everything you found: each paper, article, and thread "
        "worth a reader's attention, with its URL, who produced it, what it "
        "says, and why it matters. Finish with a short synthesis of where "
        "this topic stands right now."
    )

    messages = [{"role": "user", "content": prompt}]
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        thinking={"type": "adaptive"},
        output_config={"effort": "medium"},
        tools=[WEB_SEARCH_TOOL],
        messages=messages,
    )

    # Server-side web_search runs its own tool loop; resume on pause_turn
    # rather than treating it as done (see shared/tool-use-concepts.md).
    while response.stop_reason == "pause_turn":
        messages = [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": response.content},
        ]
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            thinking={"type": "adaptive"},
            output_config={"effort": "medium"},
            tools=[WEB_SEARCH_TOOL],
            messages=messages,
        )

    return "\n\n".join(
        block.text for block in response.content if block.type == "text"
    )


def _structure(client, topic, research):
    """Pass 2: turn the research into structured items for the page.

    Kept as a separate tool-free call so the JSON schema isn't competing with
    the server-side search loop.
    """
    prompt = (
        f'Below is research on the topic "{topic}". Convert it into a briefing.\n\n'
        "One item per paper, article, or thread worth the reader's attention, "
        "ordered most to least important. Use the real URL for each. Do not "
        "invent items that aren't in the research, and don't include an item "
        "if you have no URL for it.\n\n"
        "Verdicts: must_read = central to the topic; worth_a_skim = useful "
        "context; radar = tangential but worth knowing exists.\n\n"
        f"{research}"
    )
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        thinking={"type": "adaptive"},
        output_config={
            "effort": "medium",
            "format": {"type": "json_schema", "schema": BRIEFING_SCHEMA},
        },
        messages=[{"role": "user", "content": prompt}],
    )
    return parse_json_response(response, "briefing")


def _to_articles(items):
    """Map briefing items onto the shape the renderers expect."""
    articles = []
    for item in items:
        articles.append(
            {
                "id": item["url"],
                "title": item["title"],
                "authors": [item["author"]] if item["author"] else [],
                "url": item["url"],
                "source": item["source"],
                "tldr": item["body"],
                "body": item["body"],
                "why_it_matters": item["why_it_matters"],
                "worth_score": max(1, min(10, item["worth_score"])),
                "verdict": item["verdict"] if item["verdict"] in VERDICTS else "radar",
                "topics": item["topics"],
            }
        )
    articles.sort(key=lambda a: a["worth_score"], reverse=True)
    return articles


def run_topic_search(topic, client=None):
    """Run an on-demand research briefing for a keyword/phrase.

    Combines an arXiv keyword search with Claude's web_search tool (general
    web + best-effort Twitter/X mentions - not true trending data, since that
    requires the paid X API). Writes both a Markdown and a newspaper-style
    HTML briefing to reports/ and returns (html_path, md_path, markdown_text).
    """
    client = client or anthropic.Anthropic()

    papers = search_papers(topic, TOPIC_ARXIV_MAX_RESULTS)
    research = _research(client, topic, _format_arxiv_hits(papers))
    briefing = _structure(client, topic, research)

    articles = _to_articles(briefing["items"])
    takeaway = briefing["takeaway"]
    date_str = datetime.date.today().isoformat()
    title = f"Topic Briefing: {topic}"

    markdown = build_markdown(date_str, articles, title=title, standfirst=takeaway)
    page = build_html(
        date_str,
        articles,
        {"masthead": topic.title(), "tagline": "A Topic Briefing"},
        standfirst=takeaway,
    )

    slug = _slugify(topic)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    md_path = os.path.join(REPORTS_DIR, f"topic-{slug}-{date_str}.md")
    html_path = os.path.join(REPORTS_DIR, f"topic-{slug}-{date_str}.html")
    with open(md_path, "w") as f:
        f.write(markdown)
    with open(html_path, "w") as f:
        f.write(page)

    return html_path, md_path, markdown


if __name__ == "__main__":
    import sys

    args = [a for a in sys.argv[1:] if a]
    if not args:
        raise SystemExit('Usage: python -m daily_digest.topic_search "keyword or phrase"')
    html_path, md_path, text = run_topic_search(" ".join(args))
    print(f"Wrote {md_path}")
    print(f"Wrote {html_path}")
    print()
    print(text)
