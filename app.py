from flask import Flask, render_template, request
import feedparser
import html
from datetime import datetime, timedelta
import os
import openai

app = Flask(__name__)

# 🔑 OpenAI API Key (Render → Environment Variables에 설정)
openai.api_key = os.environ.get("OPENAI_API_KEY")

# =====================
# 카테고리 정의
# =====================
CATEGORIES = {
    "한라대": ["한라대", "한라대학교"],
    "대학이슈": ["대학", "대학교", "총장", "캠퍼스"],
    "교육": ["교육", "교육부", "학습", "교과"],
    "청년": ["청년", "취업", "청년정책"],
    "정책": ["정책", "정부", "지원"]
}

# =====================
# 유틸 함수
# =====================
def parse_date(entry):
    try:
        if entry.get("published_parsed"):
            return datetime(*entry.published_parsed[:6])
    except:
        pass
    return None

def format_date(dt):
    if not dt:
        return "날짜 정보 없음"
    return dt.strftime("%Y.%m.%d. %H:%M")

def contains_keyword(text, keywords):
    return any(k in text for k in keywords)

def ai_summary(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "뉴스 기사를 2~3줄로 요약해줘."},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content
    except:
        return "요약 정보를 불러올 수 없습니다."

# =====================
# 라우트
# =====================
@app.route("/")
def index():
    return render_template("index.html", articles=[], categories=CATEGORIES)

@app.route("/search")
def search():
    query = request.args.get("query", "")
    category = request.args.get("category")
    ai_mode = request.args.get("ai") == "1"

    feeds = [
        ("Google News", f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"),
        ("Daum News", f"https://news.daum.net/rss/search?q={query}")
    ]

    articles = []
    seen = set()
    now = datetime.now()

    for source, url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = html.unescape(entry.title)
            text = title + entry.get("summary", "")
            date = parse_date(entry)

            if title in seen:
                continue

            # 카테고리 필터
            if category and not contains_keyword(text, CATEGORIES.get(category, [])):
                continue

            # 24시간 필터
            if ai_mode and date:
                if date < now - timedelta(hours=24):
                    continue

            seen.add(title)

            summary = ai_summary(text) if ai_mode else ""

            articles.append({
                "source": source,
                "title": title,
                "date": format_date(date),
                "link": entry.link,
                "summary": summary,
                "parsed_date": date or datetime.min
            })

    articles.sort(key=lambda x: x["parsed_date"], reverse=True)

    return render_template(
        "index.html",
        articles=articles,
        categories=CATEGORIES,
        query=query,
        selected_category=category,
        ai_mode=ai_mode
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
