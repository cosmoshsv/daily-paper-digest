import datetime
import os

from daily_digest.arxiv_client import fetch_papers
from daily_digest.config import ARXIV_CATEGORIES, ARXIV_MAX_FETCH, REPORTS_DIR, TOP_N
from daily_digest.report import build_markdown
from daily_digest.summarizer import rank_and_summarize


def run():
    papers = fetch_papers(ARXIV_CATEGORIES, ARXIV_MAX_FETCH)
    if not papers:
        raise SystemExit("No papers fetched from arXiv — aborting.")

    ranked = rank_and_summarize(papers, TOP_N)

    date_str = datetime.date.today().isoformat()
    markdown = build_markdown(date_str, ranked)

    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_path = os.path.join(REPORTS_DIR, f"{date_str}.md")
    with open(report_path, "w") as f:
        f.write(markdown)

    print(f"Wrote {report_path}")
    print()
    print(markdown)
    return report_path, ranked


if __name__ == "__main__":
    run()
