import keyring
from openai import OpenAI
from langchain_community.chat_models import ChatOllama
from pymongo import MongoClient
import datetime

client = MongoClient(host='localhost', port=27017)
db = client['test']
collection = db['NewsAnalysis']

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

def prompting(news, llm='llama'):
    
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

def main():
    news = """삼성이 퀄컴, 구글과 스마트 글래스 개발을 위해 협력 중인 것으로 전해졌다.

미국 경제매체 CNBC는 현지시간 5일 크리스티아노 아몬 퀄컴 최고경영자(CEO)가 퀄컴의 반도체 개발자들이 삼성, 구글과 스마트폰과 연동되는 혼합현실(MR) 스마트 글래스 개발을 위해 협력 중이라고 밝혔다고 보도했다.

보도에 따르면, 아몬 CEO는 "스마트폰을 가진 모든 사람이 그것과 함께 사용할 수 있는 스마트 글래스를 갖게 하는 것이 협력의 목표"라고 밝혔다.

스마트 글래스 관련 구체적인 협력 방향은 아직 논의 중인 것으로 알려졌지만, 새로운 스마트 글래스는 기존 스마트 글래스와 달리 일반적인 안경이나 선글라스 같은 형태가 될 것으로 예측된다.

앞서 올해 초 출시된 애플의 스마트 글래스 '비전 프로'가 얼굴 전면부를 거의 덮는 등의 이유로 큰 대중적 호응을 얻지 못한 만큼, 애플의 스마트 글래스와는 다른 형태가 될 것으로 보인다.

이와 관련해 삼성은 공식 입장을 밝히지 않았다.

이에 앞서 이들 회사는 작년 2월 협업을 통해 확장현실(XR) 생태계를 구축한다고 밝힌 바 있다. 이후 퀄컴은 혼합현실, 가상현실 경험을 제공을 가능하게 하는 '스냅드래곤 XR2+ 2세대 플랫폼'을 올해 초 공개하기도 했다."""

    answer = prompting(news, 'llama')
    answer_dict = eval(answer)
    answer_dict.update({'date': datetime.datetime.now().strftime('%Y-%m-%d')})
    answer_dict.update({'org': 'Samsung Electronics'})
    insert_id = collection.insert_one(answer_dict)
    print(insert_id)
    return

