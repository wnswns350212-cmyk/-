from flask import Flask, request, render_template_string
import requests
import os
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

app = Flask(__name__)

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "").strip()
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "").strip()

print("=== NAVER ENV CHECK ===")
print("NAVER_CLIENT_ID:", repr(NAVER_CLIENT_ID))
print("NAVER_CLIENT_SECRET:", repr(NAVER_CLIENT_SECRET))
print("=======================")

# =========================
# 네이버 API 환경변수
# =========================
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "").strip()
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "").strip()

# =========================
# 네이버 뉴스 검색 함수
# =========================
def naver_news_search(query):
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {
        "query": query,
        "display": 100,
        "sort": "date"
    }

    res = requests.get(url, headers=headers, params=params)
    res.raise_for_status()
    return res.json().get("items", [])

# =========================
# 날짜 필터 (24시간)
# =========================
def filter_24_hours(items):
    now = datetime.now()
    result = []
    for item in items:
        pub_date = parsedate_to_datetime(item["pubDate"]).replace(tzinfo=None)
        if now - pub_date <= timedelta(hours=24):
            result.append(item)
    return result

# =========================
# 메인 페이지
# =========================
@app.route("/", methods=["GET"])
def index():
    query = request.args.get("query", "").strip()
    time_filter = request.args.get("time", "all")

    articles = []
    if query:
        articles = naver_news_search(query)
        if time_filter == "24h":
            articles = filter_24_hours(articles)

    return render_template_string(TEMPLATE, articles=articles, query=query, time_filter=time_filter)

# =========================
# HTML 템플릿 (디자인 유지)
# =========================
TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>대학 뉴스 통합 검색</title>
<style>
body {
    margin: 0;
    background: #f4f6f8;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
header {
    background: #0b2c5f;
    color: white;
    padding: 20px 40px;
    font-size: 22px;
    font-weight: bold;
}
.container {
    max-width: 1000px;
    margin: 40px auto;
    background: white;
    padding: 30px;
    border-radius: 12px;
}
.search-bar {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
}
.search-bar input {
    flex: 1;
    padding: 10px;
    font-size: 16px;
}
.search-bar button {
    padding: 10px 16px;
    border-radius: 20px;
    border: none;
    cursor: pointer;
}
.btn {
    background: #e1e5ec;
}
.btn.active {
    background: #2563eb;
    color: white;
}
.article {
    border-top: 1px solid #e5e7eb;
    padding: 20px 0;
}
.article:first-child {
    border-top: none;
}
.meta {
    color: #6b7280;
    font-size: 13px;
    margin-bottom: 6px;
}
.title {
    font-size: 18px;
    font-weight: 700;
}
.desc {
    margin-top: 6px;
}
.origin {
    margin-top: 10px;
}
.origin a {
    color: #2563eb;
    text-decoration: none;
}
</style>
</head>
<body>

<header>대학 뉴스 통합 검색</header>

<div class="container">
    <form method="get" class="search-bar">
        <input name="query" value="{{ query }}" placeholder="대학명 또는 키워드 입력">
        <button class="btn {{ 'active' if time_filter=='all' else '' }}" name="time" value="all">전체</button>
        <button class="btn {{ 'active' if time_filter=='24h' else '' }}" name="time" value="24h">24시간</button>
    </form>

    {% if query and articles|length == 0 %}
        <p>검색 결과가 없습니다.</p>
    {% endif %}

    {% for a in articles %}
    <div class="article">
        <div class="meta">{{ a.pubDate }}</div>
        <div class="title">{{ a.title|safe }}</div>
        <div class="desc">{{ a.description|safe }}</div>
        <div class="origin">
            <a href="{{ a.originallink }}" target="_blank">[원본]</a>
        </div>
    </div>
    {% endfor %}
</div>

</body>
</html>
"""

# =========================
# 실행
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
