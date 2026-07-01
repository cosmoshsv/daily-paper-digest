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

## Scheduling (GitHub Actions)

`.github/workflows/daily-digest.yml` runs the digest once a day, commits the
new report, and pushes a notification via [ntfy.sh](https://ntfy.sh) (free,
no account needed).

**One-time setup:**

1. In the repo's **Settings → Secrets and variables → Actions**, add:
   - `ANTHROPIC_API_KEY` — your Anthropic API key
   - `NTFY_TOPIC` — a private topic name only you know, e.g.
     `daily-paper-digest-859747e6` (any string works; anyone who knows the
     exact topic name can read notifications sent to it, so pick something
     non-guessable rather than a plain word)
2. Install the [ntfy app](https://ntfy.sh/#subscribe) (iOS/Android/web) and
   subscribe to that same topic name.
3. **Scheduled workflows only run from the repository's default branch
   (`main`)** — merge this branch before the `cron` trigger will fire.
   Until then, you can still trigger it manually from the Actions tab
   (`workflow_dispatch`) to test it end-to-end.

The schedule (`3 13 * * *`) is 13:03 UTC — adjust the cron expression in the
workflow file to your timezone.
