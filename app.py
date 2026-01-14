from flask import Flask, render_template, request
import feedparser
from datetime import datetime
import hashlib

app = Flask(__name__)

# --------------------
# RSS 설정 (한국 기사 위주)
# --------------------
RSS_FEEDS = {
    "한라대": "https://news.google.com/rss/search?q=한라대학교&hl=ko&gl=KR&ceid=KR:ko",
    "대학이슈": "https://news.google.com/rss/search?q=대학교&hl=ko&gl=KR&ceid=KR:ko",
    "교육": "https://news.google.com/rss/search?q=교육정책&hl=ko&gl=KR&ceid=KR:ko",
    "청년": "https://news.google.com/rss/search?q=청년정책&hl=ko&gl=KR&ceid=KR:ko",
    "정책": "https://news.google.com/rss/search?q=대학+정책&hl=ko&gl=KR&ceid=KR:ko",
}

# --------------------
# 기사 수집
# --------------------
def collect_articles():
    articles = []
    seen = set()

    for category, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)

        for entry in feed.entries:
            uid = hashlib.md5(entry.link.encode()).hexdigest()
            if uid in seen:
                continue
            seen.add(uid)

            # 날짜 파싱
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])
            else:
                published = None

            articles.append({
                "title": entry.title,
                "link": entry.link,
                "category": category,
                "published": published,
            })

    # 최신순 정렬
    articles.sort(
        key=lambda x: x["published"] if x["published"] else datetime.min,
        reverse=True
    )

    return articles


# --------------------
# 메인 페이지
# --------------------
@app.route("/")
def index():
    query = request.args.get("query", "").strip()
    category = request.args.get("category", "")

    articles = collect_articles()

    # 검색 필터
    if query:
        articles = [
            a for a in articles
            if query.lower() in a["title"].lower()
        ]

    # 카테고리 필터
    if category:
        articles = [
            a for a in articles
            if a["category"] == category
        ]

    return render_template(
        "index.html",
        articles=articles,
        query=query,
        category=category
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
