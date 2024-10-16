from platform import java_ver
from gdeltdoc import GdeltDoc, Filters
from newspaper import Article
import pandas as pd

gd = GdeltDoc()

def get_urls(keyword: str, start_date: str, end_date: str):
    f = Filters(
        start_date=start_date,
        end_date=end_date,
        num_records=10,
        keyword=keyword,
        domain='nytimes.com',
        country='US'
    )

    articles = gd.article_search(f)
    return articles

def parse_text(article_df: pd.DataFrame):
    result = []
    for _, row in article_df.iterrows():
        temp = {}
        url = row['url']
        title = row['title']
        date = row['seendate']
        article = Article(url)
        article.download()
        article.parse()
        temp['title'] = title
        temp['date'] = date 
        temp['text'] = article.text 
        result.append(temp)
    return result

        