import feedparser
from datetime import datetime, timezone, timedelta
import os
import csv
import argparse

# Default comprehensive RSS feeds for Indian financial news
DEFAULT_RSS_FEEDS = [
    "https://economictimes.indiatimes.com/rss/markets.cms",
    "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146843.cms",
    "https://www.moneycontrol.com/rss/latestnews.xml",
    "https://www.moneycontrol.com/rss/MCtopnews.xml",
    "https://www.livemint.com/rss/markets",
    "https://www.livemint.com/rss/companies",
    "https://www.livemint.com/rss/money",
    "https://www.business-standard.com/rss/markets-106.rss",
    "https://www.cnbc.com/id/10000664/device/rss/rss.html",
]

# Allow override via command line (for GitHub Actions manual run)
parser = argparse.ArgumentParser()
parser.add_argument("--feeds", nargs="*", default=DEFAULT_RSS_FEEDS,
                    help="Optional list of RSS feeds to override defaults")
args = parser.parse_args()
RSS_FEEDS = args.feeds

# Paths
folder_path = "news_data"
os.makedirs(folder_path, exist_ok=True)

seen_file = os.path.join(folder_path, "seen_links.txt")  # For permanent deduplication
today_str = datetime.now().strftime("%Y-%m-%d")
daily_csv = os.path.join(folder_path, f"india_financial_news_{today_str}.csv")  # Only this file

IST_OFFSET = timedelta(hours=5, minutes=30)

# Load all previously seen links (prevents duplicates forever)
if os.path.exists(seen_file):
    with open(seen_file, "r", encoding="utf-8") as f:
        seen_links = set(line.strip() for line in f if line.strip())
else:
    seen_links = set()

new_articles = []
new_links = []

# CSV columns
fieldnames = ["title", "link", "published_ist", "summary", "source"]

for feed_url in RSS_FEEDS:
    print(f"Fetching: {feed_url}")
    feed = feedparser.parse(feed_url)

    for entry in feed.entries:
        link = entry.get("link", "").strip()
        if not link or link in seen_links:
            continue  # Skip if already saved any day

        try:
            # Parse published time
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub_utc = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            else:
                pub_utc = datetime.now(timezone.utc)
            pub_ist = pub_utc + IST_OFFSET

            summary = getattr(entry, "summary", getattr(entry, "description", "")).strip()

            article = {
                "title": entry.get("title", "").strip(),
                "link": link,
                "published_ist": pub_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
                "summary": summary,
                "source": feed_url
            }

            new_articles.append(article)
            new_links.append(link)
            seen_links.add(link)

        except Exception as e:
            print(f"Error processing entry from {feed_url}: {e}")
            continue

# Save only to today's CSV file (append if file exists)
if new_articles:
    file_exists = os.path.isfile(daily_csv)
    with open(daily_csv, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()  # Add header only on first run of the day
        writer.writerows(new_articles)

    # Update seen_links.txt with new links
    with open(seen_file, "a", encoding="utf-8") as f:
        for link in new_links:
            f.write(link + "\n")

    print(f"Saved {len(new_articles)} new articles to {daily_csv}")
else:
    print("No new articles found in this run.")
