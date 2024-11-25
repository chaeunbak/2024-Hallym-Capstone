from flask import Blueprint, request, jsonify, render_template, current_app, session
import random
import os
import json
import openai
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# OpenAI API 키 설정
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY 환경 변수가 없습니다.")
openai.api_key = api_key

# Flask Blueprint 정의
quiz_bp = Blueprint('quiz_bp', __name__)

# LLM을 사용하여 피드백 생성
def generate_feedback(question, correct):
    messages = [
        {
            "role": "system",
            "content": (
                "YOU MUST USE KOREAN. If the user is correct, do not provide feedback. "
                "you don't have to correct their answer just provid a gentle and cute response to cheer them up"
                "All sentences must be complete and written in Korean."
            )
        },
        {
            "role": "user",
            "content": (
                f"Provide feedback for the following quiz question in Korean. "
                f"Question: {question}\nCorrect: {correct}. If correct, omit feedback; if not, cheer them up."
            )
        }
    ]
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        max_tokens=150,
        temperature=0.1
    )
    feedback = response['choices'][0]['message']['content'].strip()
    return feedback

def generate_complement(question, correct):
    messages = [
        {
            "role": "system",
            "content": (
                "You are a knowledgeable assistant providing explanations "
                "you don't have to check their correct answer just give cute complement for them to keep go one"
                "YOU MUST USE KOREAN. If the user is correct, provide a positive complement. "
                "All sentences must be complete and written in Korean."
            )
        },
        {
            "role": "user",
            "content": (
                f"Provide complement for the following quiz question in Korean. "
                f"Question: {question}\nCorrect: {correct}."
            )
        }
    ]
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        max_tokens=150,
        temperature=0.5
    )
    complement = response['choices'][0]['message']['content'].strip()
    return complement

# 퀴즈 데이터 로드 함수
def load_quiz_data():
    quiz_file_path = os.path.join(current_app.root_path, 'static', 'data', 'Quiz1.json')
    with open(quiz_file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


# 퀴즈 초기화 API
@quiz_bp.route('/initialize_quiz', methods=['GET'])
def initialize_quiz():
    quiz_data = load_quiz_data()
    session['questions'] = random.sample(quiz_data["questions"], 5)  # 5개의 랜덤 질문 선택
    session['score'] = 0
    session['current_question'] = 0
    session['history'] = []  # 문제 히스토리 초기화
    return jsonify({"message": "퀴즈가 초기화되었습니다. 준비가 되셨으면 시작 버튼을 눌러주세요!"})

# 퀴즈 질문 API
@quiz_bp.route('/get_question', methods=['GET'])
def get_question():
    current_index = session.get('current_question', 0)
    questions = session.get('questions', [])
    
    if current_index >= len(questions):
        return jsonify({"error": "퀴즈가 완료되었습니다."})
    
    question_data = questions[current_index]
    return jsonify({
        "question": question_data["question"],
        "options": ["O", "X"],
        "commentary": question_data.get("commentary", "해설이 없습니다.")
    })

# 정답 확인 API
@quiz_bp.route('/check_answer', methods=['POST'])
def check_answer():
    data = request.get_json()
    user_answer = data.get("answer")
    current_index = session.get('current_question', 0)
    questions = session.get('questions', [])
    
    if current_index >= len(questions):
        return jsonify({"error": "퀴즈가 완료되었습니다."})
    
    question = questions[current_index]
    correct = question["answer"].strip().lower() == user_answer.strip().lower()

    # 히스토리에 기록
    session['history'].append({
        "question": question["question"],
        "correct": correct,
        "user_answer": user_answer,
        "correct_answer": question["answer"]
    })
    
    if correct:
        session['score'] += 1
        complement = generate_complement(question["question"], correct)
        commentary = question.get('commentary', '해설이 없습니다.')
        result = {
            "result": "!!!축하해요 정답입니다 😄!!!",
            "feedback": complement,
            "commentary": commentary,
            "score": session['score'],
            "current_question": current_index + 1
        }
    else:
        feedback = generate_feedback(question["question"], correct)
        commentary = question.get('commentary', '해설이 없습니다.')
        result = {
            "result": "오답입니다. 다시 시도해 보세요. 😯",
            "feedback": feedback,
            "commentary": commentary,
            "score": session['score'],
            "current_question": current_index + 1
        }
    
    session['current_question'] += 1
    return jsonify(result)

# 퀴즈 결과 API
@quiz_bp.route('/quiz_result', methods=['GET'])
def quiz_result():
    score = session.get('score', 0) * 20
    history = session.get('history', [])
    return jsonify({
        "score": score,
        "history": history,
        "message": f"퀴즈가 끝났습니다! 점수: {score}점"
    })
