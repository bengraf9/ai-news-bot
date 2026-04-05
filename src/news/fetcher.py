"""
News fetcher module - Fetches real-time AI news from various sources
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime
import xml.etree.ElementTree as ET
from ..logger import setup_logger


logger = setup_logger(__name__)


class NewsFetcher:
    """Fetch real-time AI news from RSS feeds and news APIs"""

    def __init__(self):
        """Initialize the news fetcher"""
        # Personalized RSS feed sources
        self.rss_feeds = {
            # --- Big Picture / World News ---
            "NPR News": "https://feeds.npr.org/1001/rss.xml",
            "BBC World News": "https://feeds.bbci.co.uk/news/world/rss.xml",

            # --- Tech: Apple Ecosystem + AI ---
            "9to5Mac": "https://9to5mac.com/feed",
            "MacRumors": "https://feeds.macrumors.com/MacRumors-All",
            "Ars Technica AI": "https://arstechnica.com/ai/feed",
            "MIT Technology Review": "https://www.technologyreview.com/feed/",
            "Hacker News 100+": "https://hnrss.org/frontpage?points=100",

            # --- Science & Space ---
            "Nature News": "https://www.nature.com/nature.rss",
            "Ars Technica Science": "https://arstechnica.com/science/feed",
            "Space.com": "https://www.space.com/feeds/all",
            "NHC Atlantic Tropical Cyclones": "https://www.nhc.noaa.gov/index-at.xml",
            
            # --- Texas Longhorns ---
            "Burnt Orange Nation": "https://www.burntorangenation.com/rss/current.xml",

            # --- Rice Owls (Google Alerts) ---
            "Rice Owls Alerts": "https://www.google.com/alerts/feeds/01673828371079161349/8261482291259039338",

            # --- San Antonio Spurs ---
            "Pounding the Rock": "https://www.poundingtherock.com/rss/current.xml",

            # --- US Soccer (USMNT & USWNT) ---
            "Stars and Stripes FC": "https://www.starsandstripesfc.com/rss/current.xml",

            # --- College Football (general) ---
            "ESPN College Football": "https://www.espn.com/espn/rss/ncf/news",

            # --- Sports (general top stories) ---
            "ESPN Top News": "https://www.espn.com/espn/rss/news",

            # --- Board Games ---
            "Board Game Beat": "https://www.wericmartin.com/rss/",
            "BoardGameWire": "https://buttondown.com/boardgamewire/rss",
        }

        # No non-English feeds needed
        self.chinese_feeds = {}
        self.japanese_feeds = {}
        self.french_feeds = {}
        self.spanish_feeds = {}
        self.german_feeds = {}
        self.korean_feeds = {}
        self.portuguese_feeds = {}
        self.italian_feeds = {}
        self.russian_feeds = {}
        self.dutch_feeds = {}
        self.arabic_feeds = {}
        self.hindi_feeds = {}


    def fetch_rss_feed(self, feed_url: str, max_items: int = 10) -> List[Dict[str, str]]:
        """
        Fetch news items from an RSS feed.

        Args:
            feed_url: URL of the RSS feed
            max_items: Maximum number of items to fetch

        Returns:
            List of news items with title, link, description, and published date
        """
        try:
            logger.info(f"Fetching RSS feed: {feed_url}")

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(feed_url, headers=headers, timeout=10)
            response.raise_for_status()

            # Parse XML
            root = ET.fromstring(response.content)

            items = []
            # Handle RSS 2.0, RDF (RSS 1.0), and Atom formats
            if root.tag == 'rss':
                # RSS 2.0 format
                news_items = root.findall('.//item')[:max_items]
                for item in news_items:
                    title = item.find('title')
                    link = item.find('link')
                    description = item.find('description')
                    pub_date = item.find('pubDate')

                    items.append({
                        'title': title.text if title is not None else '',
                        'link': link.text if link is not None else '',
                        'description': self._clean_html(description.text if description is not None else ''),
                        'published': pub_date.text if pub_date is not None else '',
                    })
            elif root.tag.endswith('}RDF') or 'rdf' in root.tag.lower():
                # RDF / RSS 1.0 format (used by Nature, etc.)
                # Items use the RSS 1.0 namespace
                rss1_ns = {'rss1': 'http://purl.org/rss/1.0/',
                           'dc': 'http://purl.org/dc/elements/1.1/'}
                rdf_items = root.findall('.//rss1:item', rss1_ns)[:max_items]
                # Fallback: try without namespace (some RDF feeds)
                if not rdf_items:
                    rdf_items = root.findall('.//item')[:max_items]
                for item in rdf_items:
                    title = item.find('rss1:title', rss1_ns)
                    if title is None:
                        title = item.find('title')
                    link = item.find('rss1:link', rss1_ns)
                    if link is None:
                        link = item.find('link')
                    description = item.find('rss1:description', rss1_ns)
                    if description is None:
                        description = item.find('description')
                    pub_date = item.find('dc:date', rss1_ns)

                    items.append({
                        'title': title.text if title is not None else '',
                        'link': link.text if link is not None else '',
                        'description': self._clean_html(description.text if description is not None else ''),
                        'published': pub_date.text if pub_date is not None else '',
                    })
            else:
                # Atom format
                namespace = {'atom': 'http://www.w3.org/2005/Atom'}
                entries = root.findall('.//atom:entry', namespace)[:max_items]
                for entry in entries:
                    title = entry.find('atom:title', namespace)
                    link = entry.find('atom:link', namespace)
                    summary = entry.find('atom:summary', namespace)
                    if summary is None:
                        summary = entry.find('atom:content', namespace)
                    updated = entry.find('atom:updated', namespace)
                    if updated is None:
                        updated = entry.find('atom:published', namespace)

                    items.append({
                        'title': title.text if title is not None else '',
                        'link': link.get('href', '') if link is not None else '',
                        'description': self._clean_html(summary.text if summary is not None else ''),
                        'published': updated.text if updated is not None else '',
                    })

            logger.info(f"Fetched {len(items)} items from RSS feed")
            return items

        except Exception as e:
            logger.error(f"Failed to fetch RSS feed {feed_url}: {str(e)}")
            return []

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text).strip()

    def fetch_recent_news(
        self,
        language: str = "en",
        max_items_per_source: int = 5
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Fetch recent AI news from all configured sources.

        Args:
            language: Language code for the response
            max_items_per_source: Maximum items to fetch per source

        Returns:
            Dictionary with 'international' and 'domestic' news lists
        """
        logger.info("Fetching recent AI news from all sources...")

        all_news = {
            'international': [],
            'domestic': []
        }

        # Fetch international news
        for source_name, feed_url in self.rss_feeds.items():
            items = self.fetch_rss_feed(feed_url, max_items_per_source)
            for item in items:
                item['source'] = source_name
                all_news['international'].append(item)

        # Fetch domestic news based on language
        language_feeds_map = {
            "zh": self.chinese_feeds,
            "ja": self.japanese_feeds,
            "fr": self.french_feeds,
            "es": self.spanish_feeds,
            "de": self.german_feeds,
            "ko": self.korean_feeds,
            "pt": self.portuguese_feeds,
            "it": self.italian_feeds,
            "ru": self.russian_feeds,
            "nl": self.dutch_feeds,
            "ar": self.arabic_feeds,
            "hi": self.hindi_feeds,
        }

        feeds = language_feeds_map.get(language)
        if not feeds:
            logger.warning(f"No domestic feeds configured for language: {language}, using international only")
            return all_news

        for source_name, feed_url in feeds.items():
            items = self.fetch_rss_feed(feed_url, max_items_per_source)
            for item in items:
                item['source'] = source_name
                all_news['domestic'].append(item)

        logger.info(
            f"Fetched {len(all_news['international'])} international news items "
            f"and {len(all_news['domestic'])} domestic ({language}) news items"
        )

        return all_news

    def format_news_for_summary(self, news_data: Dict[str, List[Dict[str, str]]]) -> str:
        """
        Format fetched news into a text suitable for AI summarization.

        Args:
            news_data: Dictionary with 'international' and 'domestic' news lists

        Returns:
            Formatted news text
        """
        formatted = "# Recent AI News Items to Summarize\n\n"

        if news_data['international']:
            formatted += "## International News\n\n"
            for i, item in enumerate(news_data['international'], 1):
                formatted += f"### {i}. {item['title']}\n"
                formatted += f"**Source:** {item['source']}\n"
                if item['description']:
                    formatted += f"**Description:** {item['description'][:300]}...\n"
                formatted += f"**Link:** {item['link']}\n"
                if item['published']:
                    formatted += f"**Published:** {item['published']}\n"
                formatted += "\n"

        if news_data['domestic']:
            formatted += "## Domestic News\n\n"
            for i, item in enumerate(news_data['domestic'], 1):
                formatted += f"### {i}. {item['title']}\n"
                formatted += f"**Source:** {item['source']}\n"
                if item['description']:
                    formatted += f"**Description:** {item['description'][:300]}...\n"
                formatted += f"**Link:** {item['link']}\n"
                if item['published']:
                    formatted += f"**Published:** {item['published']}\n"
                formatted += "\n"

        return formatted
