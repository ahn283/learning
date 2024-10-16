from openai import OpenAI
from langchain_community.chat_models import ChatOllama
import keyring
from gdeltdoc import GdeltDoc, Filters
from newspaper import Article
from pymongo import MongoClient
import datetime
from tqdm.notebook import tqdm

OPENAI_API_KEY = keyring.get_password('openai', 'key_for_windows')
gpt_model = 'gpt-3.5-turbo-0125'
llama_model = 'llama3.1'

gpt_llm = OpenAI(
    api_key=OPENAI_API_KEY
)
llama_llm = ChatOllama(
    model=llama_model
)

gd = GdeltDoc()

client = MongoClient(host='localhost', port=27017)
db = client['test']
collection = db['NewsAnalysis']


def chatgpt_generate(query):
    response = gpt_llm.chat.completions.create(
        model=gpt_model,
        messages=[
            {
                "role":"system",
                "content":"You are a helpful assistant"
            },{
                "role":"user",
                "content":query
            }
        ]
    )
    answer = response.choices[0].message.content
    return answer

def llama_generate(query):
    response = llama_llm.invoke(query)
    answer = response.content
    return answer

def get_url(keyword):
    f = Filters(
        start_date='2024-03-20',
        end_date='2024-03-25',
        num_records=10,
        keyword=keyword,
        domain='nytimes.com',
        country='US',
    )
    
    articles = gd.article_search(f)
    return articles

def url_crawling(df):
    urls = df['url']
    titles = df['title']
    texts = []
    for url in urls:
        article = Article(url)
        article.download()
        article.parse()
        texts.append(article.text)
    return texts, titles

def get_prompt(text):
    
    prompt = f'''아래 뉴스에서 기업명을 모두 추출하고, 기업에 해당하는 감성을 분석하시오.
    각 감성에 스코어링을 하시오. 각 스코어의 합은 1이 되어야 합니다. 소수점 첫번째까지만 생성하세요.
    
    # 포맷
    출력포맷은 리스트이며, 세부 내용은 다음과 같습니다.
    반드시 출력포맷만을 생성하고, 그 이외의 번호, 단어나 설명은 절대 생성하지 마시오.
    [{{"organization":<기업명>, "positive":0~1, "negative":0~1, "neutral":0~1}}, ...]

    #뉴스
    {text}'''
    
    return prompt

def analysis(orgs = ['microsoft', 'apple', 'tesla']):
    orgs = orgs
    for org in tqdm(orgs):
        df = get_url(org)
        dates = df['seendate']
        texts, titles = url_crawling(df)
        for idx, text in enumerate(texts):
            news_item = {}
            prompt = get_prompt(text)
            answer = llama_generate(prompt)
            try:
                answer_list = eval(answer)
                news_item['text'] = text 
                news_item['title'] = titles[idx]
                [item.update({'seendate': dates[idx]}) for item in answer_list]
                news_item['sentiments'] = answer_list
                news_item['date'] = datetime.datetime.now()
                insert_id = collection.insert_one(news_item)
                print(insert_id)
            except:
                continue
    return
        
    