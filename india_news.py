import feedparser
from datetime import datetime, timezone, timedelta
import os
import json
import csv

# Feeds to fetch
RSS_FEEDS = [
    # "https://www.moneycontrol.com/rss/latestnews.xml",
    "https://economictimes.indiatimes.com/rss/markets.cms",
    "https://www.business-standard.com/rss/latest-news.xml",
    "https://www.livemint.com/rss/industry",
    "https://www.cnbc.com/id/10000664/device/rss/rss.html"
]

# Output folder inside repo
folder_path = "news_data"
os.makedirs(folder_path, exist_ok=True)

# Today's date
today_str = datetime.now().strftime("%Y-%m-%d")

json_file = os.path.join(folder_path, f"india_financial_news_{today_str}.json")
csv_file = os.path.join(folder_path, f"india_financial_news_{today_str}.csv")

IST_OFFSET = timedelta(hours=5, minutes=30)

articles = []

# Fetch feeds
for feed_url in RSS_FEEDS:
    feed = feedparser.parse(feed_url)

    for entry in feed.entries:
        try:
            if hasattr(entry, "published_parsed"):
                pub_utc = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                pub_ist = pub_utc + IST_OFFSET
            else:
                pub_ist = datetime.now() + IST_OFFSET

            summary = getattr(entry, "summary", getattr(entry, "description", ""))

            articles.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": pub_ist.isoformat(),
                "summary": summary,
                "source": feed_url
            })
        except:
            continue

# # Save JSON
# with open(json_file, "w", encoding="utf-8") as f:
#     json.dump(articles, f, indent=2, ensure_ascii=False)

# Save CSV
with open(csv_file, "w", encoding="utf-8", newline="") as f:
    if articles:
        writer = csv.DictWriter(f, fieldnames=articles[0].keys())
        writer.writeheader()
        for art in articles:
            writer.writerow(art)

print(f"Saved {len(articles)} articles to {folder_path}")
