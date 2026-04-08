# Personal News Digest

A minimalist, personally filtered news pipeline. Fetches RSS feeds, uses an LLM to select and summarize only the stories that matter to *me*, and delivers the result by email.

Inspired by Ben Hecht's observation: *"Trying to understand what's going on in the world by reading the newspaper is like trying to tell what time it is by watching the second hand of the clock."* This tool watches the hour hand.

## What It Does

- **Daily digest (Mon–Sat, 7 AM CT):** Selects 5 stories from 19 RSS feeds based on a detailed personal interest profile. The top 3 get full summaries with links; the remaining 2 appear in an "Also Noted" section as headlines with links.
- **Weekly synthesis (Sunday, 8 AM CT):** Identifies 4–7 themes from the week's news — patterns and trajectories, not individual stories. Includes source links throughout and an "In Your World" section covering personal interest areas not already discussed.
- **Deduplication across runs:** Articles selected for a digest are tracked via GitHub Actions artifacts so the same story won't reappear in subsequent days' digests.
- **Time-based filtering:** Only articles published within the last 36 hours (daily) or 7.5 days (weekly) are considered, preventing stale previews from appearing after the event they preview has already happened.
- **Runs on GitHub Actions** — zero infrastructure, zero maintenance servers.
- **Costs ~$0.50/month** (Claude Haiku 4.5) or $0/month (Gemini 2.5 Flash free tier).

## Interest Profile

The LLM filters all news through this priority list (treated as a guide, not a rigid hierarchy):

1. **Texas Longhorns** — football focus, all sports welcome
2. **Apple ecosystem & AI** — product launches, capability jumps, industry shifts
3. **College football (general)** — playoff, realignment, coaching carousel
4. **Board games** — new releases, awards, conventions (euro emphasis)
5. **Hurricane / tropical weather** — only active Gulf of Mexico or Texas coast threats
6. **Science & space** — breakthroughs, discoveries, mission milestones
7. **San Antonio Spurs** — scores, trades, draft news
8. **US Soccer (USMNT & USWNT)** — results, World Cup updates
9. **Rice Owls** — only genuinely big news
10. **Big sports stories** — historic, record-breaking, transcendent

ESPN Top News stories are further filtered by sport priority (college football, NFL, NBA, and Olympics are high; auto racing and fighting sports are excluded).

**Excluded:** Celebrity news, crime, political horse-race coverage, outrage bait, opinion masquerading as news, AI hype without substance.

## RSS Feeds (19 sources)

| Category | Source | Feed |
|----------|--------|------|
| World News | NPR News | `feeds.npr.org/1001/rss.xml` |
| World News | BBC World | `feeds.bbci.co.uk/news/world/rss.xml` |
| Tech/Apple/AI | 9to5Mac | `9to5mac.com/feed` |
| Tech/Apple/AI | MacRumors | `feeds.macrumors.com/MacRumors-All` |
| Tech/Apple/AI | Ars Technica AI | `arstechnica.com/ai/feed` |
| Tech/Apple/AI | MIT Tech Review | `technologyreview.com/feed/` |
| Tech/Apple/AI | Hacker News 100+ | `hnrss.org/frontpage?points=100` |
| Science/Space | Nature News | `nature.com/nature.rss` |
| Science/Space | Ars Technica Science | `arstechnica.com/science/feed` |
| Science/Space | Space.com | `space.com/feeds/all` |
| Weather | NHC Atlantic Tropical Cyclones | `nhc.noaa.gov/index-at.xml` |
| Longhorns | Burnt Orange Nation | `burntorangenation.com/rss/current.xml` |
| Rice Owls | Google Alerts | (custom alert feed) |
| Spurs | Pounding the Rock | `poundingtherock.com/rss/current.xml` |
| US Soccer | Stars and Stripes FC | `starsandstripesfc.com/rss/current.xml` |
| College Football | ESPN CFB | `espn.com/espn/rss/ncf/news` |
| Sports General | ESPN Top News | `espn.com/espn/rss/news` |
| Board Games | Board Game Beat | `wericmartin.com/rss/` |
| Board Games | BoardGameWire | `buttondown.com/boardgamewire/rss` |

## Architecture

```
RSS Feeds (19) → Time Filter → Dedup → LLM (Stage 1: select → Stage 2: summarize) → Gmail SMTP → Inbox
                                  ↑                        |
                  GitHub Actions artifacts ←───── mark seen ┘
                        (scheduled cron)
```

Two config files drive two different behaviors:
- `config.yaml` — daily mode: select 5 stories (3 summarized + 2 "Also Noted"), 36-hour time window
- `config-weekly.yaml` — weekly mode: select 8–12 stories, 4–7 theme synthesis, 7.5-day time window

The two-stage LLM pipeline:
1. **Stage 1 (Selection):** All time-filtered, deduplicated articles are presented to the LLM with unique IDs. The LLM returns a JSON array of selected IDs based on the interest profile.
2. **Stage 2 (Summarization):** Only the selected articles are sent to the LLM with a formatting prompt for the final digest.

## Setup

### 1. Get API Keys

- **Anthropic (Claude Haiku 4.5):** Sign up at [console.anthropic.com](https://console.anthropic.com). New accounts get $5 free credits.
- **Google (Gemini 2.5 Flash):** Sign up at [aistudio.google.com](https://aistudio.google.com). Free tier, no credit card needed.
- **Gmail App Password:** [myaccount.google.com](https://myaccount.google.com) → Security → 2-Step Verification → App passwords → create one for "Mail".

### 2. Add GitHub Secrets

Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Value |
|--------|-------|
| `ANTHROPIC_API_KEY` | Your Claude API key |
| `GOOGLE_API_KEY` | Your Gemini API key |
| `GMAIL_ADDRESS` | Your Gmail address |
| `GMAIL_APP_PASSWORD` | 16-character app password |
| `EMAIL_TO` | Recipient email address |

### 3. Test

Go to **Actions** tab → select either workflow → click **"Run workflow"** → check your inbox.

During the testing period, both Claude and Gemini run in parallel. You'll receive emails tagged `[Claude]` and `[Gemini]` so you can compare quality side by side.

### 4. After Testing: Pick a Winner

Delete the losing provider's job from each workflow file:
- In `.github/workflows/daily-news.yml`, delete either `daily-claude` or `daily-gemini`
- In `.github/workflows/weekly-news.yml`, delete either `weekly-claude` or `weekly-gemini`
- Update the remaining job's `EMAIL_SUBJECT` to remove the `[Provider]` tag

## Schedule

| Email | Schedule | Cron (UTC) |
|-------|----------|------------|
| Daily digest | Mon–Sat 7:00 AM CT | `0 12 * * 1-6` |
| Weekly synthesis | Sunday 8:00 AM CT | `0 13 * * 0` |

*Note: Cron uses CDT (UTC-5). Adjust to `0 13 * * 1-6` and `0 14 * * 0` during CST (Nov–Mar).*

## Key Files

| File | Purpose |
|------|---------|
| `config.yaml` | Daily prompts, interest profile, time window (36h) |
| `config-weekly.yaml` | Weekly prompts, thematic synthesis rules, time window (7.5d) |
| `src/news/fetcher.py` | RSS feed list, XML parsing (RSS 2.0, RDF, Atom), time-based filtering |
| `src/news/generator.py` | Two-stage LLM pipeline, dedup integration |
| `src/news/dedup.py` | Article deduplication via URL+title hashing |
| `main.py` | Entry point, config loading, notification dispatch |
| `.github/workflows/daily-news.yml` | Mon–Sat cron, artifact-based dedup persistence |
| `.github/workflows/weekly-news.yml` | Sunday cron, artifact-based dedup persistence |

## Customization

### Change story count
Edit `config.yaml` → stage1 prompt → change "exactly 5" to your preferred number. Adjust the stage2 prompt's "top 3" / "Also Noted" split accordingly.

### Change time window
Edit `max_hours` in `config.yaml` (daily) or `config-weekly.yaml` (weekly). The `max_items_per_source` setting acts as a safety cap and can usually be left at its default.

### Add/remove feeds
Edit `src/news/fetcher.py` → `self.rss_feeds` dictionary.

### Change interests
Edit the interest profile in `config.yaml` (daily) and `config-weekly.yaml` (weekly).

### Change schedule
Edit the `cron` lines in `.github/workflows/daily-news.yml` and `weekly-news.yml`.

### Adjust ESPN sport priorities
Edit the "ESPN TOP NEWS SPORT PRIORITIES" section in the stage1 prompt of `config.yaml` and `config-weekly.yaml`.

## Maintenance

**Monthly (~15 min):** Check Actions run history for failures. Usually a broken RSS feed URL — just swap in a new one.

**Quarterly:** Re-read prompts in `config.yaml` and `config-weekly.yaml`. Still match your interests?

**Seasonal:** Adjust for sports cadence (CFB offseason, World Cup, etc.). The NHC hurricane feed is always polling but only surfaces stories during active Gulf/Texas threats.

## Cost

| Component | Monthly Cost |
|-----------|-------------|
| GitHub Actions (public repo) | $0.00 |
| Gemini 2.5 Flash (free tier) | $0.00 |
| Claude Haiku 4.5 | ~$0.50–2.00 |
| Gmail SMTP | $0.00 |

## Decisions & Tradeoffs

- **Public repo** to preserve GitHub Actions private-repo minutes for other projects.
- **Time-based filtering over fixed counts** so fast feeds (BBC, NPR) aren't truncated and slow feeds (board games, Rice Owls) don't serve stale articles.
- **Dedup via GitHub Actions artifacts** rather than committing a state file to the repo. Artifacts persist 10 days and are downloaded cross-run via the GitHub REST API (`gh` CLI).
- **Separate dedup artifacts per provider** (`seen-articles-claude`, `seen-articles-gemini`) during parallel testing so the providers don't interfere with each other's state.
- **Burnt Orange Nation kept** despite high volume — alternatives (Longhorns Wire, Hookem, Barking Carnival) appear inactive. Prompt filtering handles analysis-heavy content.
- **AP Top News removed** — consistently failed with CAPTCHA challenges from GitHub Actions. NPR + BBC cover the beat well.
- **Nature News** required an RDF parser — the upstream code only handled RSS 2.0 and Atom. Fixed in `fetcher.py`.
- **NHC hurricane feed** always polls but is prompt-filtered to only surface during active Gulf/Texas threats, so it's invisible outside hurricane season.
- **Hacker News** articles are evaluated on their underlying news content; the LLM is explicitly instructed to ignore upvote counts, comment counts, and community reaction metadata.

## Credits

Forked from [giftedunicorn/ai-news-bot](https://github.com/giftedunicorn/ai-news-bot). Heavily customized with different feeds, prompts, schedule, dual-provider testing, time-based filtering, cross-run deduplication, and ESPN sport prioritization.
