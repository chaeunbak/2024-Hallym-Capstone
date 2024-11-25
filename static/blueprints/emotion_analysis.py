from flask import Blueprint, request, jsonify
import os
from dotenv import load_dotenv
import openai

# .env 파일 로드
load_dotenv()

# API 키 로드
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY 환경 변수가 없습니다.")

openai.api_key = api_key

# Flask Blueprint 정의
emotion_analysis_bp = Blueprint('emotion_analysis_bp', __name__)

class EmotionAnalysis:
    def __init__(self):
        self.model = "gpt-4o-mini"

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

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=0.3
            )

            emotion = response['choices'][0]['message']['content'].strip().lower()

            if emotion not in ["joy", "sadness", "anger"]:
                raise ValueError(f"Unexpected emotion: {emotion}")

            return emotion

        except openai.OpenAIError as e:
            print(f"OpenAI API Error: {e}")
            return None

    def respond_based_on_emotion(self, emotion, text):
        try:
            messages = [
                {"role": "system", "content": "You are a compassionate assistant who considers emotions when responding. Always reply in Korean."},
                {"role": "user", "content": (
                    f"The user's emotion is {emotion}. "
                    "Based on this emotion and the situation described below, provide a thoughtful response in Korean:\n\n"
                    f"Situation: \"{text}\""
                )}
            ]

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

# Flask 엔드포인트 정의
@emotion_analysis_bp.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    user_input = data.get("user_input", "")

    analyzer = EmotionAnalysis()
    emotion = analyzer.analyze_emotion(user_input)
    response_data = {}

    if emotion:
        response_data["emotion"] = emotion
        follow_up = analyzer.respond_based_on_emotion(emotion, user_input)
        response_data["follow_up"] = follow_up
    else:
        response_data["error"] = "감정을 인식하지 못했습니다. 다시 입력해 주세요."

    return jsonify(response_data)

# emotion_analysis.py에 추가할 엔드포인트

@emotion_analysis_bp.route('/respond', methods=['POST'])
def respond():
    data = request.get_json()
    emotion = data.get("emotion", "")
    user_input = data.get("user_input", "")

    analyzer = EmotionAnalysis()
    if emotion and user_input:
        response = analyzer.respond_based_on_emotion(emotion, user_input)
        return jsonify({"response": response})
    else:
        return jsonify({"error": "감정과 상황 정보가 올바르게 전달되지 않았습니다. 다시 시도해 주세요."}), 400
