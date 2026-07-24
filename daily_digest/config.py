import os

# arXiv categories to pull from. Start with AI/ML/NLP; add more as needed
# (e.g. "cs.CV", "cs.RO", "stat.ML").
ARXIV_CATEGORIES = ["cs.AI", "cs.LG", "cs.CL"]

# How many of the most recently submitted papers to fetch before ranking.
ARXIV_MAX_FETCH = 50

# Maximum papers to feature in the final digest (fewer if it's a slow day).
TOP_N = 5

# Claude model used to rank and summarize the fetched abstracts.
CLAUDE_MODEL = "claude-opus-4-8"

# How many arXiv keyword-search hits to pull in for an on-demand topic search.
TOPIC_ARXIV_MAX_RESULTS = 15

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(_ROOT, "reports")
DOCS_DIR = os.path.join(_ROOT, "docs")
