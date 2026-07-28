# daily-paper-digest

A personal research digest: pulls the latest arXiv papers, ranks them by how
much they're worth *your* time against an interest profile you control, and
publishes a styled daily page plus Markdown reports.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in ANTHROPIC_API_KEY, or `ant auth login`
```

Then edit **`profile.yaml`** — this is the heart of the ranking. List the
topics you're actively learning (with optional notes), plus anything that
should always be surfaced or always skipped. You can also set `masthead` and
`tagline` to name your paper. Papers are scored 1–10 against this profile and
tagged with a signal: **Must-read**, **Recommended**, or **On radar**. The
digest never pads — if only three papers clear the bar, you get three.

The HTML output is laid out as a newspaper broadsheet: top-scoring paper runs
as the lead story with a drop cap, the rest fill three columns, and Source /
Signal filter pills at the top let you narrow the page to must-reads only.
Because it's a browsable front page rather than a shortlist, `TOP_N` defaults
to 14 — lower it in `daily_digest/config.py` if you'd rather have a tight
list.

## Run

```bash
./run.sh                          # build today's digest and open it in your browser
./run.sh "speculative decoding"   # on-demand topic briefing, also opens as a page
./run.sh --no-open                # build only, skip the browser
```

`run.sh` creates a `.venv` on first run, installs dependencies (and reinstalls
only when `requirements.txt` changes), loads `.env`, builds the digest, and
opens `docs/index.html`. It handles macOS, Linux, WSL, and Git Bash.

Or drive it directly:

```bash
python main.py
```

Each run:

1. Fetches recent submissions for the configured arXiv categories **plus** a
   recent-papers keyword search per profile topic (so interests outside
   cs.AI/LG/CL still show up), deduplicated.
2. Has Claude score every candidate against `profile.yaml`.
3. Writes:
   - `reports/YYYY-MM-DD.md` — Markdown digest
   - `reports/YYYY-MM-DD.html` — styled standalone page (archived)
   - `docs/index.html` — always the latest digest, ready for GitHub Pages

### GitHub Pages (optional, one-time)

After merging to `main`: **Settings → Pages → Deploy from a branch →
`main` / `docs`**. Your latest digest is then always at
`https://<user>.github.io/daily-paper-digest/`.

## Configuration

Edit `daily_digest/config.py`:

- `ARXIV_CATEGORIES` — arXiv category codes for the firehose fetch
  (default: `cs.AI`, `cs.LG`, `cs.CL`).
- `ARXIV_MAX_FETCH` — how many recent category papers to fetch before ranking.
- `TOP_N` — maximum papers per digest (fewer on slow days).
- `CLAUDE_MODEL` — which Claude model ranks and summarizes.
- `TOPIC_ARXIV_MAX_RESULTS` — how many arXiv hits to pull in per on-demand
  topic search (below).

## On-demand topic search

For a topic you want to dig into right now (not just the daily digest),
just ask in a Claude Code session — e.g. "search for recent work on
speculative decoding" — and it runs:

```bash
python -m daily_digest.topic_search "speculative decoding"
```

This combines an arXiv keyword search with Claude's web_search tool (general
web + news), then writes both `reports/topic-<slug>-<date>.md` and a
newspaper-style `reports/topic-<slug>-<date>.html` — same layout as the daily
digest, with the topic as the masthead, the synthesis running as a dek under
it, and the Source filter split across arXiv / Web / X.

**Twitter/X caveat:** there's no free official API for real trending-topic
data, so the "Twitter/X Chatter" section is a best-effort web-search
approximation (whatever's indexed on the open web) — not live trends. If you
get an X API bearer token later, this can be upgraded to real trend/recent
tweet search.

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
