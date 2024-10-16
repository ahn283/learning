import json
import sys
import time

from bs4 import BeautifulSoup
from selenium import webdriver
# selenium v.3
# from webdriver_manager.chrome import ChromeDriverManager



class Crawler:
    
    def __init__(self, name, url):
        
        self.name = name
        self.url = url
        
    def crawl_yanolja_reviews(self):
        review_list = []
        driver = webdriver.Chrome()
        # selenium v.3
        # driver = webdriver.Chrome(ChromeDriverManager().install())
        driver.get(self.url)
        
        time.sleep(3)
        
        scroll_count = 20
        for i in range(scroll_count):
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            time.sleep(2)
            
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        review_contrainers = soup.select('#__next > section > div > div.css-1js0bc8 > div > div > div')
        review_date = soup.select('#__next > section > div > div.css-1js0bc8 > div > div > div > div.css-15duhp1 > div > p')
        
        for i in range(len(review_contrainers)):
            review_text = review_contrainers[i].find('p', class_='content-text').text
            review_stars = review_contrainers[i].find_all('path', {'fill': '#FDBD00'})
            star_cnt = len(review_stars)
            date = review_date[i].text
            
            review_dict = {
                'review': review_text,
                'stars': star_cnt,
                'date': date
            }
            
            review_list.append(review_dict)
            
        with open(f'./res/{self.name}.json', 'w') as f:
            json.dump(review_list, f, indent=4, ensure_ascii=False)
        

# def crawl_yanolja_reviews(name, url):
#     review_list = []
#     # driver = webdriver.Chrome()
#     driver = webdriver.Chrome(ChromeDriverManager().install())
#     driver.get(url)
    
#     time.sleep(3)
    
#     scroll_count = 20
#     for i in range(scroll_count):
#         driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
#         time.sleep(2)
        
#     html = driver.page_source
#     soup = BeautifulSoup(html, 'html.parser')
#     review_contrainers = soup.select('#__next > section > div > div.css-1js0bc8 > div > div > div')
#     review_date = soup.select('#__next > section > div > div.css-1js0bc8 > div > div > div > div.css-15duhp1 > div > p')
    
#     for i in range(len(review_contrainers)):
#         review_text = review_contrainers[i].find('p', class_='content-text').text
#         review_stars = review_contrainers[i].find_all('path', {'fill': '#FDBD00'})
#         star_cnt = len(review_stars)
#         date = review_date[i].text
        
#         review_dict = {
#             'review': review_text,
#             'stars': star_cnt,
#             'date': date
#         }
        
#         review_list.append(review_dict)
        
#     with open(f'./res/{name}.json', 'w') as f:
#         json.dump(review_list, f, indent=4, ensure_ascii=False)
        
        
# if __name__ == '__main__':
#     name, url = sys.argv[1], sys.argv[2]
#     crawl_yanolja_reviews(name=name, url=url)