"""
Article deduplication across daily runs.
Uses a JSON file of seen article URLs/titles, persisted via GitHub Actions artifacts.
"""

import json
import os
import hashlib
from datetime import datetime, timedelta


SEEN_FILE = os.getenv("SEEN_ARTICLES_PATH", "data/seen_articles.json")
# How many days to remember articles (prevents the file from growing forever)
RETENTION_DAYS = 7


def _hash_article(url: str, title: str) -> str:
    """Create a stable hash from URL and title."""
    key = f"{url.strip().lower()}|{title.strip().lower()}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def load_seen_articles() -> dict:
    """Load the seen articles file. Returns {hash: date_string}."""
    if not os.path.exists(SEEN_FILE):
        return {}
    try:
        with open(SEEN_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_seen_articles(seen: dict):
    """Save seen articles, pruning entries older than RETENTION_DAYS."""
    cutoff = (datetime.now() - timedelta(days=RETENTION_DAYS)).strftime("%Y-%m-%d")
    pruned = {h: d for h, d in seen.items() if d >= cutoff}

    os.makedirs(os.path.dirname(SEEN_FILE) or ".", exist_ok=True)
    with open(SEEN_FILE, "w") as f:
        json.dump(pruned, f, indent=2)


def filter_unseen(articles: list, seen: dict) -> list:
    """
    Filter out articles that have already been seen.

    Args:
        articles: list of dicts, each with at least 'url'/'link' and 'title' keys
        seen: dict of {hash: date_string} from load_seen_articles()

    Returns:
        list of articles not in the seen set
    """
    unseen = []
    for article in articles:
        url = article.get("url", article.get("link", ""))
        title = article.get("title", "")
        h = _hash_article(url, title)
        if h not in seen:
            unseen.append(article)
    return unseen


def mark_as_seen(articles: list, seen: dict) -> dict:
    """
    Mark articles as seen by adding them to the seen dict.

    Args:
        articles: list of article dicts that were selected/processed
        seen: existing seen dict

    Returns:
        Updated seen dict
    """
    today = datetime.now().strftime("%Y-%m-%d")
    for article in articles:
        url = article.get("url", article.get("link", ""))
        title = article.get("title", "")
        h = _hash_article(url, title)
        seen[h] = today
    return seen
