import os
import feedparser
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, request
from bs4 import BeautifulSoup
from openai import OpenAI

# --------------------
# 기본 설정
# --------------------
app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 국내 언론 RSS (한국어만)
RSS_FEEDS = [
    "https://news.google.com/rss/search?q=site:ac.kr&hl=ko&gl=KR&ceid=KR:ko",
    "https://news.google.com/rss/search?q=대학&hl=ko&gl=KR&ceid=KR:ko",
    "https://news.google.com/rss/search?q=대학교&hl=ko&gl=KR&ceid=KR:ko",
]

# 대학 실무 중요 키워드 (TOP5 판단용)
IMPORTANT_KEYWORDS = [
    "교육부", "평가", "재정", "정원", "입시", "등록금",
    "국책사업", "글로컬", "대학혁신", "대학구조개혁",
    "연구", "산학", "총장", "감사", "정책", "법안"
]

# --------------------
# 유틸 함수
# --------------------
def is_korean(text):
    return any("가" <= ch <= "힣" for ch in text)

def fetch_article_text(url):
    try:
        r = requests.get(url, timeout=5)
        soup = BeautifulSoup(r.text, "html.parser")
        paragraphs = soup.find_all("p")
        return " ".join(p.get_text() for p in paragraphs)
    except:
        return ""

def ai_summary(text, max_len=3):
    prompt = f"""
다음은 한국 대학과 관련된 언론 기사이다.
홍보팀·기획처 내부 참고용으로 핵심만 {max_len}문장으로 요약하라.
과도한 해석이나 감정 표현 없이 사실 중심으로 작성하라.

기사 내용:
{text[:3000]}
"""
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content.strip()

# --------------------
# 기사 수집
# --------------------
def collect_articles():
    articles = []
    now = datetime.now()

    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for e in feed.entries:
            title = e.title
            link = e.link

            # 한국어 기사만
            if not is_korean(title):
                continue

            # 날짜 (최근 24시간)
            published = getattr(e, "published_parsed", None)
            if not published:
                continue
            dt = datetime(*published[:6])
            if dt < now - timedelta(hours=24):
                continue

            content = fetch_article_text(link)
            if not is_korean(content):
                continue

            summary = ai_summary(content, max_len=2)

            articles.append({
                "title": title,
                "link": link,
                "summary": summary,
                "content": content,
                "published": dt.strftime("%Y-%m-%d %H:%M")
            })

    return articles

# --------------------
# TOP5 선정
# --------------------
def select_top5(articles):
    scored = []

    for a in articles:
        score = 0
        text = a["title"] + " " + a["content"]

        for kw in IMPORTANT_KEYWORDS:
            if kw in text:
                score += 1

        if score > 0:
            scored.append((score, a))

    scored.sort(key=lambda x: x[0], reverse=True)
    top5 = [a for _, a in scored[:5]]

    for a in top5:
        a["top_summary"] = ai_summary(a["content"], max_len=4)

    return top5

# --------------------
# 라우팅
# --------------------
@app.route("/")
def index():
    query = request.args.get("query", "")
    top5_flag = request.args.get("top5")

    articles = collect_articles()

    if query:
        articles = [a for a in articles if query in a["title"]]

    top5 = []
    if top5_flag:
        top5 = select_top5(articles)

    return render_template(
        "index.html",
        articles=articles,
        top5=top5,
        query=query
    )

# --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
