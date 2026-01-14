from flask import Flask, render_template, request, jsonify
import os
import openai

app = Flask(__name__)

# OpenAI API Key (Render Environment Variable)
openai.api_key = os.getenv("OPENAI_API_KEY")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/ai-summary", methods=["POST"])
def ai_summary():
    data = request.json
    articles = data.get("articles", "")

    if not articles.strip():
        return jsonify({"result": "❗ 기사 내용이 없습니다."})

    prompt = f"""
다음은 최근 24시간 이내 뉴스 기사 모음이다.

너는 '대학 뉴스 큐레이터 AI'다.

요구사항:
1. 전체 기사 흐름을 5줄 이내로 요약
2. 대학, 교육, 청년, 연구, 입시, 취업, 캠퍼스, 교수, 정부 교육 정책과
   직접적으로 관련된 기사만 선별
3. 중요도가 높은 기사 TOP 5를 선정
4. 각 기사마다 아래 형식으로 작성

형식:
[24시간 대학 핵심 브리핑]

[전체 요약]
- bullet 형식 5줄 이내

[대학 중요 기사 TOP 5]
1️⃣ 제목
- 핵심 요약: (2줄)
- 대학에 중요한 이유: (1줄)

기사 내용:
{articles}
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        result = response.choices[0].message.content
        return jsonify({"result": result})

    except Exception as e:
        return jsonify({"result": f"❌ 오류 발생: {str(e)}"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
