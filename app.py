from flask import Flask, render_template, request
from datetime import datetime, timedelta
import feedparser
import re

app = Flask(__name__)

RSS_URL = (
    "https://news.google.com/rss/search?"
    "q=대학교 OR 대학 OR 캠퍼스 OR 총장"
    "&hl=ko&gl=KR&ceid=KR:ko"
)

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

def clean_text(text):
    text = re.sub('<.*?>', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

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
        title = clean_text(e.title)
        summary = clean_text(e.summary)

        articles.append({
            "title": title,
            "summary": summary,
            "search_text": f"{title} {summary}".lower(),
            "url": e.link,
            "published_at": published,
            "category": classify(title)
        })

    return articles

@app.route("/")
def index():
    query = request.args.get("query", "").strip().lower()
    category = request.args.get("category", "")
    range_type = request.args.get("range", "all")

    articles = fetch_articles()

    # 🔍 검색 (가장 먼저, 가장 넓게)
    if query:
        articles = [
            a for a in articles
            if query in a["search_text"]
        ]

    # ⏰ 24시간 필터
    if range_type == "24h":
        기준 = datetime.now() - timedelta(hours=24)
        articles = [
            a for a in articles
            if a["published_at"] >= 기준
        ]

    # 🏷 카테고리 (검색 결과 기준)
    if category:
        articles = [
            a for a in articles
            if a["category"] == category
        ]

    # 최신순 정렬 (실무 중요)
    articles.sort(key=lambda x: x["published_at"], reverse=True)

    return render_template(
        "index.html",
        articles=articles,
        categories=CATEGORIES.keys(),
        query=request.args.get("query", ""),
        selected_category=category,
        range_type=range_type
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
