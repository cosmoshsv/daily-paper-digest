import json

import anthropic

from .config import CLAUDE_MODEL

RANKING_SCHEMA = {
    "type": "object",
    "properties": {
        "papers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "arxiv_id": {"type": "string"},
                    "summary": {
                        "type": "string",
                        "description": "2-3 sentence plain-language summary of the paper.",
                    },
                    "why_it_matters": {
                        "type": "string",
                        "description": "One sentence on why this paper is worth reading today.",
                    },
                },
                "required": ["arxiv_id", "summary", "why_it_matters"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["papers"],
    "additionalProperties": False,
}


def _format_abstracts(papers):
    lines = []
    for p in papers:
        lines.append(
            f"### {p['id']}\nTitle: {p['title']}\nAbstract: {p['summary']}"
        )
    return "\n\n".join(lines)


def rank_and_summarize(papers, top_n, client=None):
    """Ask Claude to pick the top_n most interesting papers and summarize each.

    Returns a list of dicts merging the model's picks with the original
    paper metadata (title, authors, url), in ranked order.
    """
    client = client or anthropic.Anthropic()

    prompt = (
        f"Below are {len(papers)} paper abstracts recently posted to arXiv. "
        f"Select the {top_n} most interesting and impactful papers for a "
        "daily research digest aimed at an AI/ML practitioner. Prioritize "
        "novelty, significance, and clarity of contribution over hype. "
        "Return them ranked from most to least important.\n\n"
        f"{_format_abstracts(papers)}"
    )

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        thinking={"type": "adaptive"},
        output_config={"effort": "medium", "format": {"type": "json_schema", "schema": RANKING_SCHEMA}},
        messages=[{"role": "user", "content": prompt}],
    )

    text = next(block.text for block in response.content if block.type == "text")
    picks = json.loads(text)["papers"]

    by_id = {p["id"]: p for p in papers}
    ranked = []
    for pick in picks[:top_n]:
        paper = by_id.get(pick["arxiv_id"])
        if paper is None:
            continue
        ranked.append(
            {
                **paper,
                "summary_short": pick["summary"],
                "why_it_matters": pick["why_it_matters"],
            }
        )
    return ranked
