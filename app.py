from flask import Flask, request, render_template
import requests
import os
from datetime import datetime, timedelta
from dateutil import parser

app = Flask(__name__)

NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET")

NAVER_NEWS_API = "https://openapi.naver.com/v1/search/news.json"

CATEGORIES = {
    "전체": [],
    "한라대": ["한라대학교", "한라대"],
    "대학이슈": ["대학", "대학교", "캠퍼스"],
    "교육": ["교육부", "교육정책", "교육"],
    "청년": ["청년", "청년정책"],
    "정책": ["정책", "정부"]
}

def fetch_news(query, display=100):
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {
        "query": query,
        "display": display,
        "sort": "date"
    }
    res = requests.get(NAVER_NEWS_API, headers=headers, params=params)
    if res.status_code != 200:
        return []

    items = res.json().get("items", [])
    articles = []

    for item in items:
        try:
            published = parser.parse(item["pubDate"])
        except:
            continue

        articles.append({
            "title": item["title"].replace("<b>", "").replace("</b>", ""),
            "summary": item["description"].replace("<b>", "").replace("</b>", ""),
            "link": item["link"],
            "date": published
        })

    return articles


def filter_by_time(articles, mode):
    if mode != "24h":
        return articles

    limit = datetime.now() - timedelta(hours=24)
    return [a for a in articles if a["date"] >= limit]


def filter_by_category(articles, category):
    if category == "전체":
        return articles

    keywords = CATEGORIES.get(category, [])
    result = []

    for a in articles:
        text = a["title"] + a["summary"]
        if any(k in text for k in keywords):
            result.append(a)

    return result


@app.route("/", methods=["GET"])
def index():
    query = request.args.get("query", "")
    category = request.args.get("category", "전체")
    time_mode = request.args.get("time", "all")

    articles = []
    if query:
        articles = fetch_news(query)
        articles = filter_by_time(articles, time_mode)
        articles = filter_by_category(articles, category)

        articles.sort(key=lambda x: x["date"], reverse=True)

    return render_template(
        "index.html",
        articles=articles,
        query=query,
        category=category,
        time_mode=time_mode,
        categories=CATEGORIES.keys()
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
