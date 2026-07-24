import xml.etree.ElementTree as ET

import requests

ARXIV_API_URL = "http://export.arxiv.org/api/query"

ATOM_NS = "http://www.w3.org/2005/Atom"


def _text(elem, tag):
    node = elem.find(f"{{{ATOM_NS}}}{tag}")
    return node.text.strip() if node is not None and node.text else ""


def _parse_feed(content):
    root = ET.fromstring(content)
    papers = []
    for entry in root.findall(f"{{{ATOM_NS}}}entry"):
        arxiv_url = _text(entry, "id")
        arxiv_id = arxiv_url.rstrip("/").split("/")[-1]
        authors = [
            _text(author, "name")
            for author in entry.findall(f"{{{ATOM_NS}}}author")
        ]
        papers.append(
            {
                "id": arxiv_id,
                "title": " ".join(_text(entry, "title").split()),
                "authors": authors,
                "summary": " ".join(_text(entry, "summary").split()),
                "published": _text(entry, "published"),
                "url": arxiv_url,
            }
        )
    return papers


def _query(search_query, sort_by, max_results):
    params = {
        "search_query": search_query,
        "sortBy": sort_by,
        "sortOrder": "descending",
        "max_results": max_results,
    }
    response = requests.get(ARXIV_API_URL, params=params, timeout=30)
    response.raise_for_status()
    return _parse_feed(response.content)


def fetch_papers(categories, max_results):
    """Fetch the most recently submitted arXiv papers for the given categories.

    Returns a list of dicts: {id, title, authors, summary, published, url}.
    """
    search_query = " OR ".join(f"cat:{c}" for c in categories)
    return _query(search_query, "submittedDate", max_results)


def search_papers(query, max_results, sort_by="relevance"):
    """Search arXiv for papers matching a free-text keyword/phrase across all fields.

    sort_by: "relevance" (default) or "submittedDate".
    Returns a list of dicts: {id, title, authors, summary, published, url}.
    """
    escaped = query.replace('"', '')
    search_query = f'all:"{escaped}"' if " " in escaped else f"all:{escaped}"
    return _query(search_query, sort_by, max_results)


def fetch_candidate_papers(categories, profile, max_category_results, max_per_topic=10):
    """Build the candidate pool for the daily digest.

    Combines the recent-submissions firehose for the configured categories
    with a recent-first keyword search per profile topic (so topics outside
    the categories, e.g. q-bio or quant-ph interests, still show up).
    Deduplicates by arXiv id, preserving first-seen order.
    """
    seen = {}
    for paper in fetch_papers(categories, max_category_results):
        seen.setdefault(paper["id"], paper)
    for topic in profile["topics"]:
        try:
            hits = search_papers(topic["name"], max_per_topic, sort_by="submittedDate")
        except requests.RequestException:
            continue  # one bad topic query shouldn't sink the digest
        for paper in hits:
            seen.setdefault(paper["id"], paper)
    return list(seen.values())
