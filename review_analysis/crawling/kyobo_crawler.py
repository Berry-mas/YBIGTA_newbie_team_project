from review_analysis.crawling.base_crawler import BaseCrawler
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import pandas as pd
import time
import csv
from utils.logger import setup_logger  # 위치에 따라 경로 다를 수 있음


chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
logger = setup_logger('kyobo.log')

class KyoboCrawler(BaseCrawler):
    def __init__(self, output_dir: str):
        super().__init__(output_dir)
        self.base_url = 'https://product.kyobobook.co.kr/detail/S000000610612'
        self.reviews_data = []
        
    def start_browser(self):
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), 
                                       options=chrome_options)
        self.driver.get(self.base_url)
        try:
            self.driver.maximize_window()
        except:
            pass
        time.sleep(2)

    
    def scrape_reviews(self):
        self.start_browser() 
        # 리뷰 섹션까지 스크롤

        wait = WebDriverWait(self.driver, 10)

        self.driver.execute_script("window.scrollTo(0, 9700)")
        time.sleep(3)
        
        like_sort_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ui-id-41-button"]')))
        like_sort_button.click() 
        recent_sort_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ui-id-43"]')))
        recent_sort_button.click()

        
        click_counts = 0
        max_clicks = 51
        while True :
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            review_blocks = soup.select(".comment_list .comment_item")

            for block in review_blocks:
    
                # 리뷰 텍스트
                text_elem = block.find("div", attrs={"class": "comment_text"})
                if text_elem:
                    review_text = text_elem.text.strip()
                else :
                    review_text = None
                    logger.warning(f'{click_counts+1}번째 페이지에서 리뷰 가져올 때 문제 발생')
                    continue

                # 날짜
                info_items = block.find_all("span", attrs={"class": "info_item"})
                if len(info_items) >= 2:
                    date = info_items[1].get_text(strip=True)
                else:
                    date = None
                    logger.warning(f'{click_counts+1}번째 페이지에서 날짜 가져올 때 문제 발생')
                    continue

                # 별점
                score_elem = block.find("span", attrs={"class": "filled-stars"})
                if score_elem:
                    style = score_elem.get("style", "")
                    if "width" in style:
                        percent = int(style.split(":")[1].replace("%", "").replace(";", "").strip())
                        score = percent / 10  # 100% → 10.0
                else: 
                    score = None
                    logger.warning(f'{click_counts+1}번째 페이지에서 별점 가져올 때 문제 발생')
                    continue

                self.reviews_data.append({
                    "text": review_text,
                    "date": date,
                    "score": score
                })

                time.sleep(0.3)

            # 더보기 버튼 시도
            try:
                more_btn = self.driver.find_element(By.XPATH, '//*[@id="ReviewList1"]/div[3]/div[2]/div/div[2]/button[2]')
                if not more_btn.is_enabled():
                    logger.info("더보기 버튼이 비활성화되어 있음 → 종료")
                    break
                
                self.driver.execute_script("arguments[0].click();", more_btn)
                time.sleep(1.5)  # AJAX 로딩 대기
                click_counts += 1
            except Exception as e:
                logger.error("더보기 버튼 없음 또는 클릭 실패 → 종료:", exc_info=True)
                break

            # 반복 조건
            if click_counts >= max_clicks:
                logger.info("최대 클릭 수 도달 → 종료")
                break

        self.driver.quit()    
    
    def save_to_database(self):
        df = pd.DataFrame(self.reviews_data)
        df.drop_duplicates(inplace=True)
        df.to_csv('reviews_kyobo.csv', encoding='utf-8-sig', index=False, quoting=csv.QUOTE_ALL)
        logger.info(f"저장 완료: 총 {len(df)}개의 리뷰")
