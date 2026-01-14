import os
import requests
from flask import Flask, render_template, request
from datetime import datetime, timedelta
from dateutil import parser

app = Flask(__name__)

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

NAVER_NEWS_URL = "https://openapi.naver.com/v1/search/news.json"

# 대학 실무용 카테고리 맵
CATEGORIES = {
    "전체": [],
    "입시·교육정책": ["입시", "수능", "교육부", "정책"],
    "대학운영·행정": ["대학", "총장", "이사회", "행정"],
    "평생교육·RISE": ["평생교육", "RISE", "지역혁신"],
    "연구·산학협력": ["연구", "산학", "협약", "기술이전"],
    "학생·캠퍼스": ["학생", "캠퍼스", "동아리"]
}

def naver_search(query, display=100):
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {
        "query": query,
        "display": display,
        "sort": "date"
    }
    r = requests.get(NAVER_NEWS_URL, headers=headers, params=params, timeout=10)
    r.raise_for_status()
    return r.json().get("items", [])

def clean_item(item):
    return {
        "title": item["title"].replace("<b>", "").replace("</b>", ""),
        "desc": item["description"].replace("<b>", "").replace("</b>", ""),
        "link": item["originallink"] or item["link"],
        "pubDate": parser.parse(item["pubDate"])
    }

@app.route("/", methods=["GET"])
def index():
    q = request.args.get("query", "").strip()
    cat = request.args.get("category", "전체")
    time_mode = request.args.get("time", "all")  # all | 24h

    items = []
    if q:
        raw = naver_search(q)
        items = [clean_item(x) for x in raw]

    # 카테고리 필터
    if cat != "전체" and items:
        keys = CATEGORIES.get(cat, [])
        items = [
            x for x in items
            if any(k in (x["title"] + x["desc"]) for k in keys)
        ]

    # 24시간 필터
    if time_mode == "24h" and items:
        cutoff = datetime.now() - timedelta(hours=24)
        items = [x for x in items if x["pubDate"] >= cutoff]

    return render_template(
        "index.html",
        items=items,
        query=q,
        category=cat,
        time_mode=time_mode,
        categories=CATEGORIES.keys()
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
