from flask import Flask, request, jsonify, render_template
import os
from markupsafe import Markup
from dotenv import load_dotenv
import openai
from flask_cors import CORS
from blueprints.emotion_analysis import emotion_analysis_bp
from blueprints.recommendation import recommendation_bp
from blueprints.quiz import quiz_bp
from blueprints.recommendation import RecommendationSystem
from blueprints.CocktailR import cocktail_recipe_bp
from blueprints.chatbot import bar_bp

# .env 파일 로드
load_dotenv()

# API 키 로드
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY 환경 변수가 없습니다.")

openai.api_key = api_key

app = Flask(__name__)
app.secret_key = "asdf6as4df5asdf16"


CORS(app)
app.register_blueprint(emotion_analysis_bp, url_prefix='/emotion')
app.register_blueprint(recommendation_bp, url_prefix='/recommend')
app.register_blueprint(quiz_bp, url_prefix='/quiz')
app.register_blueprint(cocktail_recipe_bp, url_prefix='/cocktail')
app.register_blueprint(bar_bp, url_prefix='/bar')

@app.route('/')
def intro():
    return render_template('intro.html')

@app.route('/main')
def main_page():
    return render_template('main.html')

@app.route('/main2')
def recipe():
    return render_template('main2.html')

@app.route('/main3')
def quiz():
    return render_template('main3.html')

@app.route('/main4')
def bar():
    return render_template('main4.html')



if __name__ == '__main__':
    app.run(debug=True)

# 감정 분석 및 추천 시스템 초기화
analyzer = emotion_analysis_bp()
recommender = recommendation_bp()

class EmotionAnalysis:
    def __init__(self):
        self.model = "gpt-4o-mini"  # gpt-4o-mini 모델 사용

    def analyze_emotion(self, text):
        try:
            messages = [
                {"role": "system", "content": "You are a helpful assistant that identifies emotions."},
                {"role": "user", "content": (
                    "Analyze the following text and determine if the emotion is one of the following: "
                    "joy, sadness, or anger. Only return one of these three emotions.\n\n"
                    f"Text: \"{text}\""
                )}
            ]

            # API 호출
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=0.3
            )
            
            emotion = response['choices'][0]['message']['content'].strip().lower()
            print(f"Detected emotion: {emotion}")  # 감정 로그 추가
            
            if emotion not in ["joy", "sadness", "anger"]:
                print(f"Unexpected emotion detected: {emotion}")
                return None
            
            return emotion

        except openai.OpenAIError as e:
            print(f"OpenAI API Error: {e}")
            return None

    def respond_based_on_emotion(self, emotion, text):
        try:
            # 감정을 고려한 응답 생성 (한국어로만 응답하도록 지시 추가)
            messages = [
                {"role": "system", "content": "You are a compassionate assistant who considers emotions when responding. Always reply in Korean."},
                {"role": "user", "content": (
                    f"The user's emotion is {emotion}. "
                    "Based on this emotion and the situation described below, provide a thoughtful response in Korean:\n\n"
                    f"Situation: \"{text}\""
                )}
            ]
            
            # API 호출
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=0.7
            )
            
            reply = response['choices'][0]['message']['content'].strip()
            return reply

        except openai.OpenAIError as e:
            print(f"OpenAI API Error: {e}")
            return "죄송합니다, 응답을 생성할 수 없습니다."

@app.route('/')
def intro():
    return render_template('intro.html')

@app.route('/main')
def main_page():
    return render_template('main.html')

@app.route('/main3')
def quiz():
    return render_template('main3.html')

@app.route('/analyze_and_recommend', methods=['POST'])
def analyze_and_recommend():
    data = request.get_json()
    user_input = data.get("user_input", "")

    # 감정 분석 수행
    emotion = analyzer.analyze_emotion(user_input)
    response_data = {}

    if emotion:
        response_data["emotion"] = emotion
        follow_up = analyzer.respond_based_on_emotion(emotion, user_input)
        response_data["follow_up"] = follow_up

        # 선호도에 대한 질문 추가
        response_data["ask_preference"] = "주류 추천을 위해 선호도를 알려주세요. 예를 들어, 단맛이 좋아, 쓰고 상큼한 게 좋아, 이런 식으로 답변해주시면 돼요!"
    else:
        response_data["error"] = "감정을 인식하지 못했습니다. 다시 입력해 주세요."

    return jsonify(response_data)
    return jsonify(response_data)

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json()
    emotion = data.get("emotion", "")
    flavor_input = data.get("flavor_input", "")

    # 로그 추가
    print(f"Received emotion: {emotion}, flavor input: {flavor_input}")

    if not emotion or not flavor_input:
        return jsonify({"error": "감정과 선호도가 올바르게 전달되지 않았습니다. 다시 시도해 주세요."}), 400

    # 주류 추천 수행
    recommendation = analyzer.recommend(emotion, flavor_input)
    response_data = {
        "recommendation": recommendation["text"],  # 텍스트만 반환
        "image_url": recommendation.get("image_url", "")  # 이미지 URL 반환
    }

    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True)
