from flask import Flask, render_template, request
import requests
from datetime import datetime, timedelta
from dateutil import parser

app = Flask(__name__)

NAVER_CLIENT_ID = "YOUR_CLIENT_ID"
NAVER_CLIENT_SECRET = "YOUR_CLIENT_SECRET"

def naver_search(query):
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {
        "query": query,
        "display": 100,
        "sort": "date"
    }
    res = requests.get(url, headers=headers, params=params)
    return res.json().get("items", [])

def classify(title):
    if "평생교육" in title or "RISE" in title:
        return "평생교육"
    if "입시" in title or "수능" in title:
        return "입시"
    if "대학" in title or "대학교" in title:
        return "대학정책"
    return "기타"

@app.route("/")
def index():
    query = request.args.get("query", "")
    time_filter = request.args.get("time", "all")
    category = request.args.get("category", "전체")

    articles = []
    if query:
        raw = naver_search(query)
        now = datetime.now()

        for r in raw:
            pub = parser.parse(r["pubDate"]).replace(tzinfo=None)
            if time_filter == "24h" and pub < now - timedelta(hours=24):
                continue

            cat = classify(r["title"])
            if category != "전체" and cat != category:
                continue

            articles.append({
                "title": r["title"].replace("<b>", "").replace("</b>", ""),
                "summary": r["description"].replace("<b>", "").replace("</b>", ""),
                "date": pub.strftime("%Y.%m.%d %H:%M"),
                "category": cat,
                "link": r["originallink"]
            })

    return render_template(
        "index.html",
        articles=articles,
        query=query,
        time_filter=time_filter,
        category=category
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
