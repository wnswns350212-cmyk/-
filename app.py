from flask import Flask, render_template, request
from datetime import datetime, timedelta
import feedparser
import re

app = Flask(__name__)

RSS_URL = "https://news.google.com/rss/search?q=대학교&hl=ko&gl=KR&ceid=KR:ko"

CATEGORIES = {
    "입시": ["수능", "입시", "정시", "수시"],
    "교육/수업": ["교육", "수업", "강의"],
    "연구/학술": ["연구", "학술", "논문"],
    "산학협력": ["협약", "산학", "기업"],
    "국제교류": ["국제", "교류"],
    "대학정책/행정": ["총장", "정책", "행정"],
    "평생교육": ["평생교육", "자격"],
    "지역사회": ["지역", "지자체"]
}

def clean_html(text):
    return re.sub('<.*?>', '', text)

def classify(title):
    for c, keys in CATEGORIES.items():
        if any(k in title for k in keys):
            return c
    return "기타"

def fetch_articles():
    feed = feedparser.parse(RSS_URL)
    articles = []

    for e in feed.entries:
        published = datetime(*e.published_parsed[:6])
        articles.append({
            "title": clean_html(e.title),
            "summary": clean_html(e.summary),
            "url": e.link,
            "published_at": published,
            "category": classify(e.title)
        })
    return articles

@app.route("/")
def index():
    query = request.args.get("query", "")
    category = request.args.get("category", "")
    range_type = request.args.get("range", "all")

    articles = fetch_articles()

    # 검색
    if query:
        articles = [
            a for a in articles
            if query.lower() in a["title"].lower()
            or query.lower() in a["summary"].lower()
        ]

    # 카테고리
    if category:
        articles = [a for a in articles if a["category"] == category]

    # 24시간
    if range_type == "24h":
        기준 = datetime.now() - timedelta(hours=24)
        articles = [a for a in articles if a["published_at"] >= 기준]

    return render_template(
        "index.html",
        articles=articles,
        categories=CATEGORIES.keys(),
        query=query,
        selected_category=category,
        range_type=range_type
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
