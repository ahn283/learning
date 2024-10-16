import keyring
from openai import OpenAI
from langchain_community.chat_models import ChatOllama

llm_openai = OpenAI(api_key=keyring.get_password('openai', 'key_for_windows'))
llm_llama = ChatOllama(model='llama3.1')

def get_answer_from_gpt(prompt):
    response = llm_openai.chat.completions.create(
        model='gpt-4o',
        messages=[{
            "role":"system",
            "content":"You are an helpful assistant"
        }, {
            "role":"user",
            "content":prompt
        }]
    )
    return response.choices[0].message.content

def get_answer_from_llama(prompt):
    response = llm_llama.invoke(prompt)
    return response.content

def prompt(news, llm='llama'):
    
    prompt = f"""아래 뉴스 텍스트를 참고하여 세 가지 task를 수행하시오. 출력 포맷에 정의된 것만 생성하시오.
    
    Task #1. 텍스트를 참고해서 다음과 같은 카테고리로 분류하시오. 아래 카테고리에 해당하지 않으면, 빈 리스트를 반환하시오.
    
    카테고리 : 정책/금융, 채권/외환, IB/기업, 증권, 국제뉴스, 해외주식, 부동산
    
    Task #2. 뉴스 내용을 최대 3문장으로 요약하시오.
    
    Task #3. 뉴스에서 금융 이벤트 예시를 참고하여 내용과 관련된 이벤트를 생성하시오.
    예시에 있는 이벤트가 아닌 뉴스와 관련된 이벤트 문구를 반드시 새로 생성하시오.
    
    금융 이벤트 예시: 금융 이벤트 예시: "신제품 출시", "기업 인수합병", "리콜", "배임횡령", "오너 리스크", "자연재해", "제품 불량" 등

출력 포맷:
{{"문서 카테고리": <카테고리>, "요약": <요약 문장>, "주요 이벤트": [<이벤트1>, <이벤트2>, ...]}}

뉴스:
{news}
    """
    if llm == 'llama':
        answer = get_answer_from_llama(prompt)
        return answer
    elif llm == 'gpt':
        answer = get_answer_from_gpt(prompt)
        return answer
    else:
        print("Not supported")
        return None
    