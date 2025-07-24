from review_analysis.crawling.base_crawler import BaseCrawler
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import pandas as pd


class yes24Crawler(BaseCrawler):
    def __init__(self, output_dir: str):
        super().__init__(output_dir)
        self.base_url = 'https://www.yes24.com/product/goods/13137546'
        
    def start_browser(self):
        '''
        셀레니움 정해둔 url 창을 키는 함수\n
        화면 최대
        '''
        chrome_options = Options()

        chrome_options.add_experimental_option("detach", True)
        chrome_options.add_experimental_option("excludeSwitches",["enable-logging"])

        self.driver = webdriver.Chrome(options=chrome_options)

        url = self.base_url
        self.driver.get(url)
        self.driver.maximize_window()

    def scrape_reviews(self):
        ''''
        구매자들의 리뷰를 긁어옴
        1. rate(별점)
        2. day(날짜)
        3. review(리뷰 내용)\n
        위의 내용들을 dataframe으로 저장
        '''
        self.start_browser()

        columns = ['rate', 'day', 'review']         
        values = []

        wait = WebDriverWait(self.driver, 10)                                   

        while True:
            try:
                for review_number in range(2,12):
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    parent = soup.find('div', id='infoset_reviewContentList')
                    data_rows = parent.find_all('div', class_=['reviewInfoGrp','lnkExtend'])

                    for i, row in enumerate(data_rows):
                        blank = []

                        rate = row.find('span', attrs={'class':'review_rating'})
                        if rate:
                            rate = rate.get_text().strip()
                            blank.append(rate)
                        else:
                            blank.append('Something is wrong')
                            print('{}번째 리뷰 가져올때 문제발생'.format(i+1))
                            continue
                        
                        day = row.find('em', attrs={'class':'txt_date'})
                        if day:
                            day = day.get_text().strip()
                            blank.append(day)
                        else:
                            blank.append('Something is wrong')
                            print('{}번째 리뷰 가져올때 문제발생'.format(i+1))
                            continue

                        cont = row.select_one('div.reviewInfoBot.origin div.review_cont')
                        if cont:
                            cont = cont.get_text().strip()
                            blank.append(cont)
                        else:
                            blank.append('Something is wrong')
                            print('{}번째 리뷰 가져올때 문제발생'.format(i+1))
                            continue

                        values.append(blank)

                    next_review_button = self.driver.find_element(By.XPATH, f'//*[@id="infoset_reviewContentList"]/div[1]/div[1]/div/a[{review_number+1}]')
                    wait.until(EC.element_to_be_clickable((By.XPATH, f'//*[@id="infoset_reviewContentList"]/div[1]/div[1]/div/a[{review_number+1}]')))
                    next_review_button.click()
                    wait.until(EC.staleness_of(next_review_button))

            except:
                print(f"더 이상 페이지가 없습니다.")
                break
        self.result = pd.DataFrame(values, columns = columns)
        self.driver.quit()
            
    def save_to_database(self):
        '''
        크롤링한 내용을 reviews_yes24.csv로 저장
        '''
        output_file = os.path.join(self.output_dir, "reviews_yes24.csv")
        self.result.to_csv(output_file, index=False, encoding="utf-8-sig")
