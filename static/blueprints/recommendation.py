from flask import Blueprint, request, jsonify, url_for, current_app
import json
import os
import random

# Flask Blueprint 정의
recommendation_bp = Blueprint('recommendation_bp', __name__)

class RecommendationSystem:
    def __init__(self):
        self.model = "gpt-4o-mini"

    def load_data(self, file_key):
        # url_for을 사용해서 정적 파일 경로 가져오기
        with current_app.app_context():
            file_url = url_for('static', filename=f'data/{file_key}')
            file_path = os.path.join(current_app.root_path, file_url.lstrip("/"))
            
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)

    def recommend(self, emotion, user_input):
        file_key_map = {
            "joy": "Makgeolli.json",
            "sadness": "Chungju.json",
            "anger": "Soju.json"
        }
        file_key = file_key_map.get(emotion)
        if not file_key:
            return "추천할 주류 문서를 찾을 수 없습니다."

        drinks = self.load_data(file_key)
        recommendation = random.choice(drinks)

        return {
            "text": (
                f"추천 주류: {recommendation['name']}\n"
                f"종류: {recommendation['type']}\n"
                f"알콜 도수: {recommendation['alcohol_content']}%\n"
                f"지역: {recommendation['region']}\n"
                f"용량: {recommendation['volume']}\n"
                f"맛 설명: {recommendation['flavor_profile']['flavor_description']}\n"
                f"어울리는 음식: {', '.join(recommendation['pairing'])}\n"
                f"추천 문구: {random.choice(recommendation['recommendation_phrases'])}\n"
            ),
            "image_url": recommendation.get("image_url")
        }

@recommendation_bp.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json()
    emotion = data.get("emotion", "")
    flavor_input = data.get("flavor_input", "")

    recommender = RecommendationSystem()

    if not emotion or not flavor_input:
        return jsonify({"error": "감정과 선호도가 올바르게 전달되지 않았습니다. 다시 시도해 주세요."}), 400

    recommendation = recommender.recommend(emotion, flavor_input)
    return jsonify(recommendation)
