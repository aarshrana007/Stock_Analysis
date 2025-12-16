import feedparser
from datetime import datetime, timezone, timedelta
import os
import json
import argparse

# Default RSS feeds (comprehensive Indian + global financial news)
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

# Parse optional command-line feeds (space-separated)
parser = argparse.ArgumentParser()
parser.add_argument("--feeds", nargs="*", default=DEFAULT_RSS_FEEDS,
                    help="Optional list of RSS feeds to override defaults")
args = parser.parse_args()

RSS_FEEDS = args.feeds

# Folders and files
folder_path = "news_data"
os.makedirs(folder_path, exist_ok=True)

seen_file = os.path.join(folder_path, "seen_links.json")
master_file = os.path.join(folder_path, "all_financial_news.jsonl")  # .jsonl for line-separated

today_str = datetime.now().strftime("%Y-%m-%d")
daily_file = os.path.join(folder_path, f"financial_news_{today_str}.json")

IST_OFFSET = timedelta(hours=5, minutes=30)

# Load seen links
if os.path.exists(seen_file):
    with open(seen_file, "r", encoding="utf-8") as f:
        seen_links = set(json.load(f))
else:
    seen_links = set()

new_articles = []
new_links = []

for feed_url in RSS_FEEDS:
    feed = feedparser.parse(feed_url)
    print(f"Parsing feed: {feed_url} ({len(feed.entries)} entries)")

    for entry in feed.entries:
        link = entry.get("link", "").strip()
        if not link or link in seen_links:
            continue

        try:
            if hasattr(entry, "published_parsed"):
                pub_utc = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                pub_ist = pub_utc + IST_OFFSET
            else:
                pub_ist = datetime.now(timezone.utc) + IST_OFFSET

            summary = getattr(entry, "summary", getattr(entry, "description", ""))

            article = {
                "title": entry.get("title", ""),
                "link": link,
                "published": pub_ist.isoformat(),
                "summary": summary.strip(),
                "source": feed_url
            }
            new_articles.append(article)
            new_links.append(link)
            seen_links.add(link)
        except Exception as e:
            print(f"Error processing entry: {e}")
            continue

# Save new articles
if new_articles:
    # Append to master (line-separated JSON for easy large-file handling)
    with open(master_file, "a", encoding="utf-8") as f:
        for art in new_articles:
            json.dump(art, f, ensure_ascii=False)
            f.write("\n")

    # Save today's batch separately
    with open(daily_file, "w", encoding="utf-8") as f:
        json.dump(new_articles, f, indent=2, ensure_ascii=False)

    # Update seen links
    with open(seen_file, "w", encoding="utf-8") as f:
        json.dump(list(seen_links), f)

    print(f"Fetched and saved {len(new_articles)} new articles.")
else:
    print("No new articles this run.")

# Optional: Commit changes if you want history in repo
# (Handled in workflow below)
