from flask import Flask, request, render_template_string
import feedparser
import html
from datetime import datetime
import os

from sumy.summarizers.text_rank import TextRankSummarizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer

app = Flask(__name__)

CATEGORIES = {
    "한라대": ["한라대학교", "한라대", "HLU"],
    "대학이슈": ["대학", "대학교", "등록금", "총장", "캠퍼스"],
    "대학": ["대학", "학과", "입시"],
    "교육": ["교육", "교육부", "학교"],
    "청년": ["청년", "취업", "일자리"],
    "정책": ["정책", "정부", "지원사업"]
}

HTML = """
<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>한라대학교 뉴스</title>
<style>
body { font-family: Arial; background:#f4f7fb; margin:0 }
header { background:#0b2c5f; color:white; padding:20px; display:flex; align-items:center }
header img { height:50px; margin-right:15px }
.container { width:80%; margin:30px auto; background:white; padding:30px; border-radius:10px }
.category a { margin-right:10px; padding:8px 12px; background:#1f5fa5; color:white; text-decoration:none; border-radius:5px }
.article { border-bottom:1px solid #ddd; padding:15px 0 }
.summary { color:#444; margin-top:5px }
</style>
</head>
<body>

<header>
<img src="https://upload.wikimedia.org/wikipedia/commons/7/77/Halla_University_logo.png">
<h2>한라대학교 뉴스 아카이브</h2>
</header>

<div class="container">
<div class="category">
{% for c in categories %}
<a href="/category/{{ c }}">{{ c }}</a>
{% endfor %}
</div>

{% for a in articles %}
<div class="article">
<b>{{ a.title }}</b><br>
<small>{{ a.date }} | {{ a.source }}</small>
<p class="summary">📝 {{ a.summary }}</p>
<a href="{{ a.link }}" target="_blank">원문</a>
</div>
{% endfor %}
</div>

</body>
</html>
"""

def summarize(text):
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("korean"))
        summarizer = TextRankSummarizer()
        return " ".join(str(s) for s in summarizer(parser.document, 2))
    except:
        return "요약 정보 없음"

def collect_news(keywords):
    feeds = [
        ("Google News", "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko")
    ]

    articles = []

    for source, url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = html.unescape(entry.title)
            text = title + entry.get("summary", "")
            if not any(k in text for k in keywords):
                continue

            articles.append({
                "title": title,
                "source": source,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "summary": summarize(entry.get("summary", "")),
                "link": entry.link
            })
    return articles[:20]

@app.route("/")
def home():
    articles = collect_news(sum(CATEGORIES.values(), []))
    return render_template_string(HTML, articles=articles, categories=CATEGORIES.keys())

@app.route("/category/<name>")
def category(name):
    articles = collect_news(CATEGORIES.get(name, []))
    return render_template_string(HTML, articles=articles, categories=CATEGORIES.keys())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
