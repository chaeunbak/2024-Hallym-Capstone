from flask import Blueprint, request, jsonify, render_template
import os
import json
import openai
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# API 키 로드
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY 환경 변수가 없습니다.")

openai.api_key = api_key

# JSON 파일 로드
bar_data_path = os.path.join(os.getcwd(), 'static', 'data', 'bar.json')
with open(bar_data_path, encoding='utf-8') as f:
    bars = json.load(f)

# Flask Blueprint 설정
bar_bp = Blueprint('bar_bp', __name__)

def generate_gpt_response(prompt):
    """
    OpenAI GPT를 호출하여 자연스러운 응답을 생성하는 함수
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "너는 한국어로 답변하는 전통주 술집 챗봇입니다. 사용자의 질문에서 원하는 정보를 분석하여 전달해주세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"GPT 응답 생성 중 오류가 발생했습니다: {str(e)}"

def is_exit_intent(user_input):
    """
    사용자의 입력이 종료 의도인지 판단
    """
    prompt = f"""
    사용자의 입력: "{user_input}"
    사용자가 대화를 종료하려는 의도가 있는지 판단해주세요.
    종료 의도를 나타내는 표현의 예:
    - 그만
    - 끝
    - 필요 없어
    - 이 정도면 됐어
    - 이제 됐어
    - 고마워
    - 안녕
    사용자의 입력이 종료 의도라면 "대화 종료", 아니라면 "대화 지속"이라고만 답변해주세요.
    """
    response = generate_gpt_response(prompt)
    return "대화 종료" in response

def extract_user_intent(user_input, bar_info):
    """
    사용자의 질문에서 의도를 추출하고 JSON 데이터에서 관련 정보를 찾음
    """
    prompt = f"""
    사용자의 질문: "{user_input}"
    다음 정보 중에서 사용자가 어떤 것을 알고 싶어하는지 판단하고, 관련 정보를 반환하세요:
    - 운영 시간
    - 전화번호
    - 위치
    - 소개
    - 예약 정보
    - 인기 메뉴
    - 추가 정보
    가게 이름: {bar_info['name']}
    가게 정보:
    - 위치: {', '.join(bar_info['location'])}
    - 전화번호: {bar_info['phone-number']}
    - 운영 시간: {bar_info['time']}
    - 소개: {bar_info['information']}
    - 예약 정보: {bar_info['reservation']}
    - 인기 메뉴: {bar_info['specialty-menu']}
    - 추가 정보: {', '.join(bar_info['more-information'])}
    
    사용자의 질문에 대해 간단히 답변하고, 추가로 정보를 물어볼 수 있도록 도와주세요.
    """
    return generate_gpt_response(prompt)

def find_bar_info(bar_name):
    """
    바 이름을 검색하여 JSON 데이터에서 해당 정보를 반환
    """
    for bar in bars:
        if bar_name in bar['name']:
            return bar
    return None

@bar_bp.route('/')
def index():
    return render_template('main4.html')

@bar_bp.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get('message')
    current_bar_name = data.get('current_bar')

    if is_exit_intent(user_input):
        return jsonify({"response": "대화를 종료합니다. 감사합니다!", "end": True})

    # 현재 대화 중인 가게가 없는 경우
    if not current_bar_name:
        bar_info = find_bar_info(user_input)
        if bar_info:
            return jsonify({
                "response": f"'{bar_info['name']}'에 대한 정보를 찾았습니다! 궁금한 내용을 물어보세요. (예: 몇 시까지 해요?, 전화번호 알려줘, 위치는 어디야? 등)",
                "current_bar": bar_info  # 바 정보 전달
            })
        else:
            return jsonify({"response": "해당 가게 정보를 찾을 수 없습니다. 다른 가게 이름을 입력해주세요."})

    # 정보 요청 처리
    current_bar = find_bar_info(current_bar_name)
    if not current_bar:
        return jsonify({"response": "현재 선택된 가게 정보를 찾을 수 없습니다. 다시 시도해주세요."})

    response = extract_user_intent(user_input, current_bar)
    return jsonify({"response": response, "current_bar": current_bar})

