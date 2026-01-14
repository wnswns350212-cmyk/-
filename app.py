from flask import Flask, request, render_template_string
import feedparser
import html
from datetime import datetime

app = Flask(__name__)

UNIVERSITY_KEYWORDS = [
    "대학", "대학교", "입시", "수시", "정시", "등록금",
    "캠퍼스", "학과", "신입생", "편입", "교육부",
    "대학원", "총장", "학사", "졸업"
]

ADMISSION_KEYWORDS = [
    "입시", "수시", "정시", "등록금", "교육부",
    "대입", "모집요강", "학생부", "논술"
]

HTML = """
<!doctype html>
<html lang="ko">
<head>
    <meta charset="utf-8">
    <title>대학교 뉴스 검색</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f7fb;
            margin: 0;
            padding: 0;
        }
        header {
            background-color: #0b2c5f;
            color: white;
            padding: 20px;
            display: flex;
            align-items: center;
        }
        header img {
            height: 50px;
            margin-right: 15px;
        }
        .container {
            width: 80%;
            margin: 30px auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
        }
        form input {
            padding: 10px;
            width: 300px;
        }
        form button {
            padding: 10px 15px;
            background-color: #1f5fa5;
            color: white;
            border: none;
            cursor: pointer;
        }
        .article {
            border-bottom: 1px solid #ddd;
            padding: 15px 0;
        }
        .source {
            color: #1f5fa5;
            font-weight: bold;
        }
        .date {
            color: #666;
            font-size: 13px;
        }
    </style>
</head>
<body>

<header>
    <img src="https://upload.wikimedia.org/wikipedia/commons/7/77/Halla_University_logo.png">
    <h2>대학교 뉴스 통합 검색</h2>
</header>

<div class="container">
    <form method="get" action="/search">
        <input type="text" name="query" placeholder="대학교 / 입시 / 교육 키워드" required>
        <label>
            <input type="checkbox" name="admission_only" value="1">
            입시·등록금 뉴스만 보기
        </label>
        <button type="submit">검색</button>
    </form>

    {% if query %}
        <h3>검색어: {{ query }}</h3>
    {% endif %}

    {% for article in articles %}
        <div class="article">
            <div class="source">[{{ article.source }}]</div>
            <b>{{ article.title }}</b><br>
            <span class="date">{{ article.date }}</span><br>
            <a href="{{ article.link }}" target="_blank">원문 보기</a>
        </div>
    {% endfor %}

    {% if query and not articles %}
        <p>조건에 맞는 대학교 뉴스가 없습니다.</p>
    {% endif %}
</div>

</body>
</html>
"""

def contains_keyword(text, keywords):
    return any(keyword in text for keyword in keywords)

def parse_date(entry):
    try:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            return datetime(*entry.published_parsed[:6])
        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            return datetime(*entry.updated_parsed[:6])
    except:
        pass
    return None

def format_date(dt):
    if not dt:
        return "날짜 정보 없음"
    return dt.strftime("%Y.%m.%d. %H:%M")

@app.route("/")
def index():
    return render_template_string(HTML, articles=[], query=None)

@app.route("/search")
def search():
    query = request.args.get("query")
    admission_only = request.args.get("admission_only")

    articles = []
    seen_titles = set()

    feeds = [
        ("Google News", f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"),
        ("Daum News", f"https://news.daum.net/rss/search?q={query}")
    ]

    for source, url in feeds:
        feed = feedparser.parse(url)

        for entry in feed.entries:
            title = html.unescape(entry.title)
            text = title + entry.get("summary", "")

            if admission_only:
                if not contains_keyword(text, ADMISSION_KEYWORDS):
                    continue
            else:
                if not contains_keyword(text, UNIVERSITY_KEYWORDS):
                    continue

            if title in seen_titles:
                continue
            seen_titles.add(title)

            parsed_dt = parse_date(entry)

            articles.append({
                "source": source,
                "title": title,
                "date": format_date(parsed_dt),
                "parsed_date": parsed_dt,
                "link": entry.link
            })

    articles.sort(key=lambda x: x["parsed_date"] or datetime.min, reverse=True)

    return render_template_string(HTML, articles=articles, query=query)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

