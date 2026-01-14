from flask import Flask, render_template, request
from datetime import datetime, timedelta
import feedparser

app = Flask(__name__)

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q=대학교&hl=ko&gl=KR&ceid=KR:ko"

CATEGORIES = {
    "입시": ["수능", "입시", "정시", "수시"],
    "교육/수업": ["교육", "수업", "강의", "커리큘럼"],
    "연구/학술": ["연구", "학술", "논문"],
    "산학협력": ["협약", "산학", "기업"],
    "국제교류": ["국제", "해외", "외국인"],
    "대학정책/행정": ["정책", "총장", "행정"],
    "평생교육": ["평생교육", "자격과정"],
    "지역사회": ["지역", "지자체"]
}

def classify_category(title):
    for category, keywords in CATEGORIES.items():
        if any(k in title for k in keywords):
            return category
    return "기타"

def fetch_articles():
    feed = feedparser.parse(GOOGLE_NEWS_RSS)
    articles = []

    for entry in feed.entries:
        published = datetime(*entry.published_parsed[:6])

        articles.append({
            "title": entry.title,
            "summary": entry.summary,
            "url": entry.link,
            "published_at": published,
            "category": classify_category(entry.title),
            "views": 0
        })
    return articles

@app.route("/")
def index():
    query = request.args.get("query", "")
    category = request.args.get("category", "")
    range_type = request.args.get("range", "all")
    scrap = request.args.get("scrap")

    articles = fetch_articles()

    if query:
        articles = [a for a in articles if query in a["title"] or query in a["summary"]]

    if category:
        articles = [a for a in articles if a["category"] == category]

    if range_type == "24h":
        기준 = datetime.now() - timedelta(hours=24)
        articles = [a for a in articles if a["published_at"] >= 기준]

    if scrap == "1":
        기준 = datetime.now() - timedelta(hours=24)
        articles = [a for a in articles if a["published_at"] >= 기준][:6]

    return render_template(
        "index.html",
        articles=articles,
        categories=CATEGORIES.keys(),
        selected_category=category,
        query=query
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
