from flask import Blueprint, request, render_template, jsonify, send_from_directory
import openai
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# OpenAI API 키 설정
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY 환경 변수가 없습니다.")
openai.api_key = api_key

# Flask Blueprint 설정
cocktail_recipe_bp = Blueprint('cocktail_recipe_bp', __name__)

# OpenAI GPT를 사용하여 응답 생성
def ask_openai_gpt(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 전문 바텐더이며, 사용자에게 전통주 기반의 칵테일을 추천해 주는 역할입니다. 응답은 친절하고 자연스럽게, 대화하듯이 제공해 주세요. 결과는 마크다운 형식이 아닌, 깔끔한 텍스트 형식으로 제공해 주세요. 제목, 재료, 만드는 방법 등을 자연스럽게 왼쪽 정렬로 나열해 주세요."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.6
        )
        return response.choices[0].message['content'].strip()
    except openai.error.AuthenticationError as e:
        print("API 키 인증 실패:", e)
    except openai.error.OpenAIError as e:
        print("OpenAI API 호출 오류:", e)
    except Exception as e:
        print("알 수 없는 오류:", e)
    return "응답 생성 중 오류가 발생했습니다."

# 메인 페이지 렌더링
@cocktail_recipe_bp.route('/main2')
def index():
    return render_template('main2.html')

# 칵테일 추천 API 엔드포인트
@cocktail_recipe_bp.route('/recommend_cocktail', methods=['POST'])
def recommend_cocktail():
    try:
        data = request.get_json()
        user_base = data.get("user_base")
        user_abv = data.get("user_abv")
        user_fruits = data.get("user_fruits")
        user_drinks = data.get("user_drinks")
        result_abv = data.get("result_abv")

        # GPT 프롬프트 생성
        prompt = f"""
        당신은 전문 바텐더이자 전통주를 기반으로 한 칵테일 바의 주인이며, 창의적이고 실용적인 레시피를 만드는 전문가입니다. 
        다음 조건을 충족하는 최적의 칵테일 레시피를 만들어야 합니다:

        1. 사용자가 제공한 베이스 술은 "{user_base}"이며, 이 술의 도수는 {user_abv}도입니다. 
        2. 사용자가 제공한 추가 재료:
           - 집에 있는 과일: {user_fruits}
           - 냉장고에 있는 음료: {user_drinks}
             음료 규칙
             1.한국에서의 사이다는 스프라이트와 동일한 개념으로 알코올이 들어있지 않습니다.
             2.주스류는 알코올이 들어있지 않습니다.

        3. 레시피 설계 조건:
           - {user_base}의 알코올 함량({user_base}*{user_abv})을 포함하여, 완성된 칵테일의 도수가 {result_abv}도와 최대한 일치해야 합니다.
           - 도수 계산을 위해 모든 액체류는 '이름: 90ml (9도) = 8.1g(알코올)' 형식으로 명확히 작성하십시오.
           - 도수 계산은 반드시 소수점 첫째 자리까지 수행합니다.
           - 모든 재료를 사용할 필요는 없으며, 가장 어울리는 조합만 선별하십시오.
           - 결과 레시피는 사용자가 집에서 쉽게 재현할 수 있어야 합니다.

        4. 출력 형식:
           - 최종 제안된 레시피는 1개만 작성하며, 레시피 이름 뒤에 참고한 기존 칵테일 이름을 명시해 출처를 알 수 있게 하십시오.
           - 제안된 레시피는 다음 형식을 따라야 합니다:
             - 칵테일 이름: "최종 칵테일 이름 (참고한 기존 칵테일 이름)"
             - 재료 목록: 각 재료와 용량, 도수, 알코올 함량 명시 (예: 와인: 90ml (9도) = 8.1g(알코올))
             - 도수 계산: 최종 칵테일의 도수 계산 과정과 결과 명확히 기술
             - 만드는 방법: 단계별 상세한 조리법 제시 (간결하면서도 사용자 친화적으로 작성)

        5. 레시피 스타일:
           - 전통주를 활용한 창의적이면서도 현대적인 칵테일로 완성되어야 합니다.
           - 기존 레시피를 참고하여 수정했음을 명확히 나타내고, 레시피의 유래를 간략히 언급하십시오.

        이 조건들을 기반으로, 사용자에게 딱 맞는 맞춤형 칵테일 레시피를 작성하십시오.
        """

        # OpenAI GPT로부터 추천 받기
        response = ask_openai_gpt(prompt)

        return jsonify({"success": True, "response": response})

    except Exception as e:
        print("오류:", e)
        return jsonify({"success": False, "error": str(e)})
