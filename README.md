# daily-paper-digest

A small agent that pulls the latest arXiv papers, has Claude pick and
summarize the top ones, and writes a dated Markdown digest into `reports/`.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in ANTHROPIC_API_KEY, or `ant auth login`
```

## Run

```bash
python main.py
```

This fetches the latest papers from arXiv (`daily_digest/config.py` controls
which categories and how many), asks Claude to rank and summarize the top 5,
and writes `reports/YYYY-MM-DD.md`.

## Configuration

Edit `daily_digest/config.py`:

- `ARXIV_CATEGORIES` — arXiv category codes to pull from (default: `cs.AI`,
  `cs.LG`, `cs.CL`). Add more, e.g. `cs.CV`, `cs.RO`.
- `ARXIV_MAX_FETCH` — how many recent papers to fetch before ranking.
- `TOP_N` — how many papers to feature in the digest.
- `CLAUDE_MODEL` — which Claude model ranks and summarizes.

## Scheduling

This repo doesn't include a scheduler yet — running `python main.py` daily is
a separate step. Options, roughly in order of robustness:

- **GitHub Actions** (recommended for "set it and forget it"): a scheduled
  workflow (`cron`) runs the script daily, commits the new report, and can
  post a notification via a service like ntfy.sh or Slack.
- **A local cron job / Task Scheduler** if you're running this from your own
  machine.

Ask if you'd like a GitHub Actions workflow added for this.
