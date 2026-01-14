import os
import html
import feedparser
from flask import Flask, render_template, request, jsonify
from datetime import datetime, date
import openai

# ======================
# 기본 설정
# ======================
app = Flask(__name__)
openai.api_key = os.environ.get("OPENAI_API_KEY")

# ======================
# 카테고리 정의
# ======================
CATEGORIES = {
    "한라대": ["한라", "한라대학교"],
    "대학이슈": ["대학", "총장", "캠퍼스", "학과"],
    "교육": ["교육부", "교육", "교원"],
    "청년": ["청년", "취업", "일자리"],
    "정책": ["정책", "지원", "재정", "법안"],
}

NEWS_FEEDS = [
    ("Google News", "https://news.google.com/rss/search?q=대학&hl=ko&gl=KR&ceid=KR:ko"),
    ("Daum News", "https://news.daum.net/rss/search?q=대학"),
]

# ======================
# 유틸 함수
# ======================
def parse_date(entry):
    try:
        if entry.get("published_parsed"):
            return datetime(*entry.published_parsed[:6])
    except:
        pass
    return None

def format_date(dt):
    return dt.strftime("%Y.%m.%d. %H:%M") if dt else "날짜 없음"

def categorize(title):
    for cat, keywords in CATEGORIES.items():
        if any(k in title for k in keywords):
            return cat
    return "기타"

def ai_summary(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "너는 대학 홍보팀을 위한 뉴스 요약 AI야."},
                {"role": "user", "content": f"다음 기사를 2~3줄로 요약해줘:\n{text}"}
            ],
            max_tokens=120
        )
        return response.choices[0].message.content.strip()
    except:
        return "요약 생성 실패"

# ======================
# 메인 뉴스 수집
# ======================
def collect_news():
    articles = []
    seen = set()

    for source, url in NEWS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = html.unescape(entry.title)
            if title in seen:
                continue
            seen.add(title)

            dt = parse_date(entry)
            summary = ai_summary(title)

            articles.append({
                "title": title,
                "source": source,
                "date": format_date(dt),
                "raw_date": dt,
                "category": categorize(title),
                "summary": summary,
                "link": entry.link
            })

    articles.sort(key=lambda x: x["raw_date"] or datetime.min, reverse=True)
    return articles

ALL_ARTICLES = collect_news()

# ======================
# 라우트
# ======================
@app.route("/")
def index():
    query = request.args.get("query", "")
    category = request.args.get("category", "")

    filtered = ALL_ARTICLES

    if query:
        filtered = [a for a in filtered if query in a["title"]]

    if category:
        filtered = [a for a in filtered if a["category"] == category]

    return render_template("index.html", articles=filtered)

@app.route("/top5")
def top5():
    today = date.today()
    today_articles = [
        a for a in ALL_ARTICLES
        if a["raw_date"] and a["raw_date"].date() == today
    ]

    prompt = "\n".join([a["title"] for a in today_articles])

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "대학 기획처를 위한 뉴스 분석 AI"},
            {"role": "user", "content": f"""
오늘 기사 중 대학에 가장 중요한 기사 5개를 선정하고
각각 2줄 요약해줘:

{prompt}
"""}
        ],
        max_tokens=500
    )

    return jsonify({"result": response.choices[0].message.content})

# ======================
# 실행
# ======================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
