import datetime
import os
import re

import anthropic

from .arxiv_client import search_papers
from .config import CLAUDE_MODEL, REPORTS_DIR, TOPIC_ARXIV_MAX_RESULTS

WEB_SEARCH_TOOL = {"type": "web_search_20260209", "name": "web_search"}


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


def run_topic_search(topic, client=None):
    """Run an on-demand research briefing for a keyword/phrase.

    Combines an arXiv keyword search with Claude's web_search tool (general
    web + best-effort Twitter/X mentions - not true trending data, since that
    requires the paid X API). Writes a Markdown briefing to reports/ and
    returns (report_path, briefing_text).
    """
    client = client or anthropic.Anthropic()

    papers = search_papers(topic, TOPIC_ARXIV_MAX_RESULTS)
    arxiv_block = _format_arxiv_hits(papers)

    prompt = (
        f'I want a research briefing on: "{topic}"\n\n'
        "Here are recent matching arXiv papers (may be incomplete or only "
        "partially relevant - use judgment about what to include):\n\n"
        f"{arxiv_block}\n\n"
        "Using the web_search tool, also look for:\n"
        "1. Recent news, blog posts, or technical discussion about this topic "
        "(prioritize the last few weeks).\n"
        "2. Any notable recent discussion of this topic on Twitter/X - search "
        "for it specifically (e.g. site:twitter.com or site:x.com, or "
        '"twitter" + the topic). This is NOT true trending-topic data (no X '
        "API access) - it's just whatever is indexed on the open web. State "
        "that caveat explicitly rather than implying it's live trend data.\n\n"
        "Then write a concise research briefing in Markdown with these "
        "section headers exactly:\n"
        "## Key Papers\n"
        "## Web & News\n"
        "## Twitter/X Chatter\n"
        "## Takeaway\n"
        "Key Papers should cover the most relevant arXiv papers above, each "
        "with a 1-2 sentence summary and a link. Web & News and Twitter/X "
        "Chatter should cite sources. Takeaway is 2-3 sentences synthesizing "
        "what's happening with this topic right now."
    )

    messages = [{"role": "user", "content": prompt}]
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
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
            max_tokens=4096,
            thinking={"type": "adaptive"},
            output_config={"effort": "medium"},
            tools=[WEB_SEARCH_TOOL],
            messages=messages,
        )

    briefing = "\n\n".join(
        block.text for block in response.content if block.type == "text"
    )

    date_str = datetime.date.today().isoformat()
    slug = _slugify(topic)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_path = os.path.join(REPORTS_DIR, f"topic-{slug}-{date_str}.md")
    with open(report_path, "w") as f:
        f.write(f"# Topic Briefing: {topic}\n*{date_str}*\n\n{briefing}\n")

    return report_path, briefing


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        raise SystemExit('Usage: python -m daily_digest.topic_search "keyword or phrase"')
    topic_arg = " ".join(sys.argv[1:])
    path, text = run_topic_search(topic_arg)
    print(f"Wrote {path}")
    print()
    print(text)
