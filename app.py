from flask import Flask, render_template, request
import feedparser
import html
import os
from datetime import datetime, timedelta
from dateutil import parser as dateparser
import openai

app = Flask(__name__)

# 🔑 OpenAI
openai.api_key = os.environ.get("OPENAI_API_KEY")

# ======================
# 키워드 / 카테고리 설정
# ======================
CATEGORIES = {
    "한라대": ["한라대학교", "한라대"],
    "대학이슈": ["대학", "대학교", "총장", "캠퍼스"],
    "대학": ["대학", "대학교"],
    "교육": ["교육부", "교육정책", "교육"],
    "청년": ["청년", "취업", "청년정책"],
    "정책": ["정부", "정책", "국회"]
}

BASE_KEYWORDS = sum(CATEGORIES.values(), [])

# ======================
# RSS (한국 뉴스 중심)
# ======================
FEEDS = [
    ("Daum", "https://news.daum.net/rss/search?q=대학"),
    ("Google", "https://news.google.com/rss/search?q=대학&hl=ko&gl=KR&ceid=KR:ko")
]

# ======================
# 유틸 함수
# ======================
def parse_date(entry):
    try:
        if hasattr(entry, "published"):
            return dateparser.parse(entry.published)
    except:
        pass
    return None

def contains_keywords(text, keywords):
    return any(k in text for k in keywords)

def ai_summary(text):
    try:
        res = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "너는 한국 대학 홍보팀·기획처를 위한 뉴스 요약 AI다."
                },
                {
                    "role": "user",
                    "content": f"""
아래 기사를 대학 실무자가 바로 이해할 수 있게
핵심만 2~3문장으로 요약해줘.

기사:
{text}
"""
                }
            ],
            temperature=0.3
        )
        return res.choices[0].message.content.strip()
    except:
        return "요약 정보를 불러오지 못했습니다."

# ======================
# 뉴스 수집
# ======================
def collect_news(category=None, only_today=False):
    articles = []
    seen = set()
    now = datetime.now()

    for source, url in FEEDS:
        feed = feedparser.parse(url)

        for e in feed.entries:
            title = html.unescape(e.title)
            summary = html.unescape(e.get("summary", ""))
            text = title + " " + summary

            if not contains_keywords(text, BASE_KEYWORDS):
                continue

            if category:
                if not contains_keywords(text, CATEGORIES.get(category, [])):
                    continue

            dt = parse_date(e)
            if only_today and (not dt or dt < now.replace(hour=0, minute=0)):
                continue

            if title in seen:
                continue
            seen.add(title)

            articles.append({
                "title": title,
                "date": dt.strftime("%Y.%m.%d. %H:%M") if dt else "날짜 없음",
                "raw_date": dt or datetime.min,
                "link": e.link,
                "summary": ai_summary(text)
            })

    articles.sort(key=lambda x: x["raw_date"], reverse=True)
    return articles

# ======================
# TOP 5 오늘의 핵심 뉴스
# ======================
def top5_today():
    today_articles = collect_news(only_today=True)
    return today_articles[:5]

# ======================
# 라우트
# ======================
@app.route("/")
def index():
    query = request.args.get("q")
    category = request.args.get("category")
    top5 = request.args.get("top5")

    if top5:
        articles = top5_today()
    else:
        articles = collect_news(category=category)

    return render_template(
        "index.html",
        articles=articles,
        categories=CATEGORIES.keys(),
        selected_category=category
    )

# ======================
# 실행
# ======================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
