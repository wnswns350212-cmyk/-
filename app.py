from flask import Flask, render_template, request
import feedparser
from datetime import datetime, timedelta
import hashlib

app = Flask(__name__)

# =========================
# 한국 기사 RSS만 사용
# =========================
RSS_FEEDS = {
    "대학": "https://news.google.com/rss/search?q=대학교&hl=ko&gl=KR&ceid=KR:ko",
    "교육정책": "https://news.google.com/rss/search?q=교육정책&hl=ko&gl=KR&ceid=KR:ko",
    "청년정책": "https://news.google.com/rss/search?q=청년정책&hl=ko&gl=KR&ceid=KR:ko",
    "대학입시": "https://news.google.com/rss/search?q=대학입시&hl=ko&gl=KR&ceid=KR:ko",
}

# =========================
# 기사 수집
# =========================
def collect_articles():
    articles = {}
    now = datetime.now()

    for category, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)

        for entry in feed.entries:
            if not hasattr(entry, "published_parsed"):
                continue

            published = datetime(*entry.published_parsed[:6])

            uid = hashlib.md5(entry.link.encode()).hexdigest()

            if uid not in articles:
                articles[uid] = {
                    "title": entry.title,
                    "link": entry.link,
                    "summary": entry.get("summary", ""),
                    "published": published,
                    "categories": {category},
                    "interest": 1
                }
            else:
                articles[uid]["categories"].add(category)
                articles[uid]["interest"] += 1

    return list(articles.values())

# =========================
# 메인 페이지
# =========================
@app.route("/")
def index():
    query = request.args.get("query", "").strip()
    filter_24h = request.args.get("filter") == "24h"
    board = request.args.get("board") == "1"

    articles = collect_articles()
    now = datetime.now()

    # 24시간 필터
    if filter_24h or board:
        articles = [
            a for a in articles
            if a["published"] >= now - timedelta(hours=24)
        ]

    # 검색 기능
    if query:
        articles = [
            a for a in articles
            if query.lower() in a["title"].lower()
        ]

    # 언론보도 스크랩 (관심도 높은 6개)
    if board:
        articles.sort(key=lambda x: x["interest"], reverse=True)
        articles = articles[:6]
    else:
        articles.sort(key=lambda x: x["published"], reverse=True)

    return render_template(
        "index.html",
        articles=articles,
        query=query,
        filter_24h=filter_24h,
        board=board
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
