from review_analysis.crawling.base_crawler import BaseCrawler
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import os
import pandas as pd
import time
import csv
from utils.logger import setup_logger  


chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
logger = setup_logger('kyobo.log')

class KyoboCrawler(BaseCrawler):
    def __init__(self, output_dir: str):
        """
        교보문고 리뷰 크롤러 초기화 함수

        Args:
            output_dir (str): 크롤링한 데이터를 저장할 디렉토리 경로
        """
        super().__init__(output_dir)
        self.base_url = 'https://product.kyobobook.co.kr/detail/S000000610612'
        self.reviews_data: List[Dict[str, Any]] = []

        
    def start_browser(self):
        """
        Selenium WebDriver를 초기화하고 해당 책 상세 페이지로 이동
        """
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), 
                                       options=chrome_options)
        self.driver.get(self.base_url)
        try:
            self.driver.maximize_window()
        except:
            pass
        time.sleep(2)

    
    def scrape_reviews(self):
        """
        교보문고 웹사이트에서 리뷰 데이터를 크롤링하여 self.reviews_data에 저장

        - 리뷰 섹션으로 스크롤
        - 정렬 방식 변경 (최근순)
        - 더보기 버튼을 누르며 리뷰 페이지 반복
        - 각 리뷰에서 텍스트, 날짜, 별점 정보 추출
        - 최대 51번 반복하며 리뷰 수집
        - 예외 발생 시 로깅 처리
        """
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
        """
        수집한 리뷰 데이터를 CSV 형식으로 저장함.

        - 중복 리뷰 제거
        - 파일명: 'reviews_kyobo.csv'
        - 저장 경로: self.output_dir 하위 경로
        """
        df = pd.DataFrame(self.reviews_data)
        df.drop_duplicates(inplace=True)

        # 절대경로로 안전하게 변환
        abs_output_dir = os.path.abspath(self.output_dir)
        os.makedirs(abs_output_dir, exist_ok=True)

        output_path = os.path.join(abs_output_dir, 'reviews_kyobo.csv')

        df.to_csv(output_path, encoding='utf-8-sig', index=False, quoting=csv.QUOTE_ALL)
        logger.info(f"저장 완료: 총 {len(df)}개의 리뷰 → {output_path}")