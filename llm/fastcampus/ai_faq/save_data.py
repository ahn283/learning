import pickle
import keyring

from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from openai import Client

from ch1.download_data import get_data
from ch1.inference import inference_json
from ch2.download_data import get_urls
from ch2.inference import inference_many_json


def main():
    url = "https://fastcampus.co.kr/data_online_llmservice"
    prompt_detail = get_data(url)
    result_text = inference_json(prompt_detail)
    
    url_list = get_urls()
    result_image = inference_many_json(url_list)
    
    result = result_text["qa_list"] + result_image["qa_list"]
    
    with open('qas.pkl', 'wb') as f:
        pickle.dump(result, f)
    
    result_questions = [row['question'] for row in result]
    
    db = FAISS.from_texts(
        result_questions,
        embedding=OpenAIEmbeddings(openai_api_key=keyring.get_password('openai', 'key_for_windows')),
        metadatas=result
    )
    db.save_local("qas.index")
    
if __name__ == '__main__':
    main()