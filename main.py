import datetime
import os

from daily_digest.arxiv_client import fetch_candidate_papers
from daily_digest.config import ARXIV_CATEGORIES, ARXIV_MAX_FETCH, DOCS_DIR, REPORTS_DIR, TOP_N
from daily_digest.html_report import build_html
from daily_digest.profile import load_profile
from daily_digest.report import build_markdown
from daily_digest.summarizer import rank_and_summarize


def run():
    profile = load_profile()
    papers = fetch_candidate_papers(ARXIV_CATEGORIES, profile, ARXIV_MAX_FETCH)
    if not papers:
        raise SystemExit("No papers fetched from arXiv — aborting.")

    ranked = rank_and_summarize(papers, TOP_N, profile)

    date_str = datetime.date.today().isoformat()
    markdown = build_markdown(date_str, ranked)
    page = build_html(date_str, ranked, profile)

    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(DOCS_DIR, exist_ok=True)

    report_path = os.path.join(REPORTS_DIR, f"{date_str}.md")
    with open(report_path, "w") as f:
        f.write(markdown)
    with open(os.path.join(REPORTS_DIR, f"{date_str}.html"), "w") as f:
        f.write(page)
    with open(os.path.join(DOCS_DIR, "index.html"), "w") as f:
        f.write(page)

    print(f"Wrote {report_path} (+ .html and docs/index.html)")
    print()
    print(markdown)
    return report_path, ranked


if __name__ == "__main__":
    run()
