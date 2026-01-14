import os
import requests
from datetime import datetime, timedelta
from flask import Flask, request, render_template

app = Flask(__name__)

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

NAVER_API_URL = "https://openapi.naver.com/v1/search/news.json"


def naver_search(query):
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }

    params = {
        "query": query,
        "display": 100,   # ⭐ 최대한 많이
        "start": 1,
        "sort": "date"    # 최신순
    }

    res = requests.get(NAVER_API_URL, headers=headers, params=params)
    res.raise_for_status()
    return res.json().get("items", [])


def parse_date(pub_date):
    return datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")


@app.route("/", methods=["GET"])
def index():
    query = request.args.get("query", "").strip()
    time_filter = request.args.get("time", "all")   # all | 24h
    category = request.args.get("category", "all")

    results = []

    if query:
        items = naver_search(query)

        now = datetime.now().astimezone()
        filtered = []

        for item in items:
            pub_date = parse_date(item["pubDate"])

            # 24시간 필터
            if time_filter == "24h":
                if pub_date < now - timedelta(hours=24):
                    continue

            # 카테고리 필터 (제목 + 설명 기준)
            if category != "all":
                text = (item["title"] + item["description"]).lower()
                if category.lower() not in text:
                    continue

            filtered.append({
                "title": item["title"],
                "description": item["description"],
                "date": pub_date.strftime("%Y-%m-%d %H:%M"),
            })

        results = filtered

    return render_template(
        "index.html",
        results=results,
        query=query,
        time_filter=time_filter,
        category=category
    )
