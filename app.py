from flask import Flask, render_template, request
from datetime import datetime, timedelta

app = Flask(__name__)

ARTICLES = [
    {
        "title": "문경대학교 평생교육원, 드론 전문인재 양성 협약",
        "summary": "문경대학교가 드론 전문인력 양성을 위해 산학 협약을 체결했다.",
        "category": "평생교육",
        "published_at": datetime(2026, 1, 14, 4, 22),
        "views": 312,
        "url": "https://news.google.com"
    },
    {
        "title": "부천대학교 RISE 평생교육센터 자격과정 성과",
        "summary": "부천대학교가 자격과정 교육생 100% 자격 취득 성과를 달성했다.",
        "category": "평생교육",
        "published_at": datetime(2026, 1, 14, 4, 14),
        "views": 420,
        "url": "https://news.google.com"
    },
    {
        "title": "2026 수능 과탐 응시자 감소",
        "summary": "수능 과탐 응시자 감소 현상이 교육 정책 논쟁으로 이어지고 있다.",
        "category": "입시",
        "published_at": datetime(2026, 1, 14, 4, 27),
        "views": 980,
        "url": "https://news.google.com"
    }
]

CATEGORIES = [
    "입시", "교육/수업", "연구/학술", "산학협력",
    "국제교류", "대학정책/행정", "평생교육", "지역사회"
]

@app.route("/")
def index():
    query = request.args.get("query", "")
    category = request.args.get("category", "")
    range_type = request.args.get("range", "all")
    scrap = request.args.get("scrap")

    result = ARTICLES

    if query:
        result = [a for a in result if query in a["title"] or query in a["summary"]]

    if category:
        result = [a for a in result if a["category"] == category]

    if range_type == "24h":
        기준 = datetime.now() - timedelta(hours=24)
        result = [a for a in result if a["published_at"] >= 기준]

    if scrap == "1":
        기준 = datetime.now() - timedelta(hours=24)
        result = [a for a in result if a["published_at"] >= 기준]
        result = sorted(result, key=lambda x: x["views"], reverse=True)[:6]

    return render_template(
        "index.html",
        articles=result,
        categories=CATEGORIES,
        selected_category=category,
        query=query,
        range_type=range_type
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
