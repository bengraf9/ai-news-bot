# Personal News Digest

A minimalist, personally filtered news pipeline. Fetches RSS feeds, uses an LLM to select and summarize only the stories that matter to *me*, and delivers the result by email.

Inspired by Ben Hecht's observation: *"Trying to understand what's going on in the world by reading the newspaper is like trying to tell what time it is by watching the second hand of the clock."* This tool watches the hour hand.

## What It Does

- **Daily digest (Mon–Sat, 7 AM CT):** Selects exactly 3 stories from 19 RSS feeds based on a detailed personal interest profile. Each story gets a 2–3 sentence summary and a link to the full article.
- **Weekly synthesis (Sunday, 8 AM CT):** Identifies 3–5 themes from the week's news — patterns and trajectories, not individual stories. Includes an "In Your World" section covering personal interest areas.
- **Runs on GitHub Actions** — zero infrastructure, zero maintenance servers.
- **Costs ~$0.50/month** (Claude Haiku 4.5) or $0/month (Gemini 2.5 Flash free tier).

## Interest Profile

The LLM filters all news through this priority list:

1. **Texas Longhorns** — football focus, all sports welcome
2. **Apple ecosystem & AI** — product launches, capability jumps, industry shifts
3. **Science & space** — breakthroughs, discoveries, mission milestones
4. **San Antonio Spurs** — scores, trades, draft news
5. **US Soccer (USMNT & USWNT)** — results, World Cup updates
6. **College football (general)** — playoff, realignment, coaching carousel
7. **Board games** — new releases, awards, conventions (euro emphasis)
8. **Rice Owls** — only genuinely big news
9. **Big sports stories** — historic, record-breaking, transcendent

**Excluded:** Celebrity news, crime, political horse-race coverage, outrage bait, opinion masquerading as news, AI hype without substance.

## RSS Feeds (19 sources)

| Category | Source | Feed |
|----------|--------|------|
| World News | AP Top News | `apnews.com/hub/ap-top-news.rss` |
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
RSS Feeds (19) → LLM (filter + summarize) → Gmail SMTP → Your Inbox
                         ↑
              GitHub Actions (scheduled cron)
```

Two config files drive two different behaviors:
- `config.yaml` — daily mode: select 3 stories, short summaries
- `config-weekly.yaml` — weekly mode: select 8–12 stories, thematic synthesis

## Setup

### 1. Get API Keys

- **Anthropic (Claude Haiku 4.5):** Sign up at [platform.claude.com](https://platform.claude.com). New accounts get $5 free credits.
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

## Maintenance

**Monthly (~15 min):** Check Actions run history for failures. Usually a broken RSS feed URL — just swap in a new one.

**Quarterly:** Re-read prompts in `config.yaml` and `config-weekly.yaml`. Still match your interests?

**Seasonal:** Adjust for sports cadence (CFB offseason, World Cup, etc.).

## Customization

### Change story count
Edit `config.yaml` → stage1 prompt → change "exactly 3" to your preferred number.

### Add/remove feeds
Edit `src/news/fetcher.py` → `self.rss_feeds` dictionary.

### Change interests
Edit the interest profile in `config.yaml` (daily) and `config-weekly.yaml` (weekly).

### Change schedule
Edit the `cron` lines in `.github/workflows/daily-news.yml` and `weekly-news.yml`.

## Cost

| Component | Monthly Cost |
|-----------|-------------|
| GitHub Actions (public repo) | $0.00 |
| Gemini 2.5 Flash (free tier) | $0.00 |
| Claude Haiku 4.5 | ~$0.50–2.00 |
| Gmail SMTP | $0.00 |

## Credits

Forked from [giftedunicorn/ai-news-bot](https://github.com/giftedunicorn/ai-news-bot). Heavily customized for personal use with different feeds, prompts, schedule, and dual-provider testing.
