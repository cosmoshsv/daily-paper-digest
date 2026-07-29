import json

import anthropic

from .config import CLAUDE_MODEL, MAX_TOKENS
from .profile import render_profile

VERDICTS = ["must_read", "worth_a_skim", "radar"]


def parse_json_response(response, what="response"):
    """Pull structured JSON out of a response, failing loudly and usefully.

    A truncated response surfaces as a bare JSONDecodeError deep in the parse,
    which says nothing about the actual cause, so check stop_reason first.
    """
    stop = getattr(response, "stop_reason", None)
    if stop == "max_tokens":
        raise SystemExit(
            f"Ran out of output tokens while writing the {what}, so the JSON was "
            "cut off mid-value.\n"
            "  Fix: raise MAX_TOKENS or lower TOP_N in daily_digest/config.py "
            f"(currently MAX_TOKENS={MAX_TOKENS})."
        )
    if stop == "refusal":
        raise SystemExit(f"The model declined to produce the {what}.")

    text = next((b.text for b in response.content if b.type == "text"), "")
    if not text.strip():
        raise SystemExit(f"The model returned no text for the {what}.")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"Could not parse the {what} as JSON: {exc}\n"
            f"  stop_reason was {stop!r}. If this repeats, raise MAX_TOKENS or "
            "lower TOP_N in daily_digest/config.py."
        ) from exc

RANKING_SCHEMA = {
    "type": "object",
    "properties": {
        "papers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "arxiv_id": {"type": "string"},
                    "tldr": {
                        "type": "string",
                        "description": "1-2 punchy sentences: what the paper does and what it found.",
                    },
                    "body": {
                        "type": "string",
                        "description": (
                            "3-5 sentences of newspaper-style prose explaining the "
                            "work: the problem, the approach, the headline result, and "
                            "the caveat or open question. Plain declarative sentences, "
                            "no bullet points, no markdown, no hype."
                        ),
                    },
                    "why_it_matters": {
                        "type": "string",
                        "description": "One sentence on why this is worth this reader's time, tied to their profile.",
                    },
                    "worth_score": {
                        "type": "integer",
                        "description": "1-10: how much this paper is worth this reader's time given their profile.",
                    },
                    "verdict": {"type": "string", "enum": VERDICTS},
                    "topics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Short topic tags; reuse the reader's profile topic names where they apply.",
                    },
                },
                "required": [
                    "arxiv_id",
                    "tldr",
                    "body",
                    "why_it_matters",
                    "worth_score",
                    "verdict",
                    "topics",
                ],
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


def rank_and_summarize(papers, top_n, profile, client=None):
    """Ask Claude to pick the papers most worth this reader's time.

    top_n is a maximum - on a slow day fewer (or zero) papers may clear the
    bar. Returns a list of dicts merging the model's picks with the original
    paper metadata, ordered by worth_score descending.
    """
    client = client or anthropic.Anthropic()

    prompt = (
        "You are curating a personal daily research digest. Here is the "
        "reader's interest profile:\n\n"
        f"{render_profile(profile)}\n\n"
        f"Below are {len(papers)} paper abstracts recently posted to arXiv. "
        f"Select AT MOST {top_n} papers that are genuinely worth this "
        "reader's time today, judged against their profile. Do not pad the "
        "list - if only three papers clear the bar, return three. Prioritize "
        "substance over hype. Skip anything matching their 'not interested' "
        "list; lean toward anything matching 'always worth surfacing'.\n\n"
        "These are laid out as a newspaper: the highest-scoring paper runs as "
        "the lead story, the rest fill the columns, and the reader can filter "
        "to must-reads. So be strict about tiering - reserve must_read for a "
        "genuine handful, not half the list.\n\n"
        "Verdicts: must_read = directly advances a profile topic and is "
        "substantial; worth_a_skim = relevant, read the intro/figures; "
        "radar = tangential but worth knowing exists.\n\n"
        f"{_format_abstracts(papers)}"
    )

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        thinking={"type": "adaptive"},
        output_config={
            "effort": "medium",
            "format": {"type": "json_schema", "schema": RANKING_SCHEMA},
        },
        messages=[{"role": "user", "content": prompt}],
    )

    picks = parse_json_response(response, "ranking")["papers"]

    by_id = {p["id"]: p for p in papers}
    ranked = []
    for pick in picks[:top_n]:
        paper = by_id.get(pick["arxiv_id"])
        if paper is None:
            continue
        ranked.append(
            {
                **paper,
                "tldr": pick["tldr"],
                "body": pick["body"],
                "why_it_matters": pick["why_it_matters"],
                "worth_score": max(1, min(10, pick["worth_score"])),
                "verdict": pick["verdict"] if pick["verdict"] in VERDICTS else "radar",
                "topics": pick["topics"],
            }
        )
    ranked.sort(key=lambda p: p["worth_score"], reverse=True)
    return ranked
