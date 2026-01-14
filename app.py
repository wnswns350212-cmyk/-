import os
import feedparser
from flask import Flask, render_template, request
from datetime import datetime, timedelta
import openai

# OpenAI 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

# ===============================
# 설정
# ===============================
RSS_FEEDS = [
    "https://news.google.com/rss/search?q=대학",
    "https://news.google.com/rss/search?q=교육",
    "https://news.google.com/rss/search?q=청년",
    "https://news.google.com/rss/search?q=정책",
    "https://news.google.com/rss/search?q=한라대학교"
]

CATEGORIES = {
    "한라대": ["한라대학교", "한라대"],
    "대학이슈": ["대학", "캠퍼스"],
    "대학": ["대학"],
    "교육": ["교육"],
    "청년": ["청년"],
    "정책": ["정책"]
}

# ===============================
# AI 요약 함수
# ===============================
def ai_summary(text):
    try:
        res = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "너는 대학 홍보팀을 돕는 뉴스 요약 AI다. 핵심만 2~3줄로 요약해라."
                },
                {
                    "role": "user",
                    "content": text[:1500]
                }
            ]
        )
        return res.choices[0].message.content.strip()
    except Exception:
        return "요약을 불러올 수 없습니다."

# ===============================
# 뉴스 수집
# ===============================
def fetch_news():
    articles = []
    seen = set()

    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for e in feed.entries:
            title = e.get("title", "")
            link = e.get("link", "")
            published = e.get("published", "")

            if title in seen:
                continue
            seen.add(title)

            try:
                pub_dt = datetime(*e.published_parsed[:6])
            except Exception:
                pub_dt = datetime.now()

            summary = ai_summary(title)

            articles.append({
                "title": title,
                "link": link,
                "published": pub_dt,
                "published_str": pub_dt.strftime("%Y.%m.%d. %H:%M"),
                "summary": summary
            })

    articles.sort(key=lambda x: x["published"], reverse=True)
    return articles

# ===============================
# 중요 기사 TOP5 (오늘 기준)
# ===============================
def top5_today(articles):
    today = datetime.now().date()
    today_articles = [a for a in articles if a["published"].date() == today]

    scored = []
    for a in today_articles:
        prompt = f"""
다음 뉴스가 대학에서 얼마나 중요한지 1~10점으로 평가해라.

뉴스 제목: {a['title']}
"""
        try:
            res = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            score = int("".join(filter(str.isdigit, res.choices[0].message.content)))
        except Exception:
            score = 0

        scored.append((score, a))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [a for _, a in scored[:5]]

# ===============================
# 메인 라우트
# ===============================
@app.route("/", methods=["GET"])
def index():
    query = request.args.get("query", "")
    category = request.args.get("category", "")
    show_top5 = request.args.get("top5")

    articles = fetch_news()

    # 검색 필터
    if query:
        articles = [a for a in articles if query in a["title"]]

    # 카테고리 필터
    if category and category in CATEGORIES:
        keywords = CATEGORIES[category]
        articles = [
            a for a in articles
            if any(k in a["title"] for k in keywords)
        ]

    top5 = top5_today(articles) if show_top5 else []

    return render_template(
        "index.html",
        articles=articles,
        categories=CATEGORIES.keys(),
        selected_category=category,
        query=query,
        top5=top5
    )

# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
