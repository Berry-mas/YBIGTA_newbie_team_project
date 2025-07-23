import time
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import StaleElementReferenceException
from review_analysis.crawling.base_crawler import BaseCrawler
from utils.logger import setup_logger  

logger = setup_logger("aladin.log")

class AladinCrawler(BaseCrawler):
    def __init__(self, output_dir: str):
        super().__init__(output_dir)
        self.base_url = 'https://www.aladin.co.kr/shop/wproduct.aspx?ItemId=40869703'
        self.driver = None
        self.reviews = []
        self.min_reviews = 600
        self.output_dir = output_dir

    def start_browser(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--lang=ko-KR")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        logger.info("Chrome 브라우저 실행 완료")

    def scrape_reviews(self):
        self.start_browser()
        self.driver.get(self.base_url)
        time.sleep(1)
        logger.info("알라딘 페이지 접속 완료")

        try:
            tab = self.driver.find_element(By.XPATH, '//a[contains(@href, "CommentReview")]')
            self.driver.execute_script("arguments[0].click();", tab)
            time.sleep(1)
            logger.info("100자평 탭 클릭 완료")
        except Exception as e:
            logger.error(f"100자평 탭 클릭 실패: {e}")
            self.driver.quit()
            return []
        
        # "전체 (634)" 탭 클릭
        try:
            total_tab = self.driver.find_element(By.ID, "tabTotal")
            self.driver.execute_script("arguments[0].click();", total_tab)
            time.sleep(1)
            logger.info("전체 탭 클릭 완료")
        except Exception as e:
            logger.warning(f"⚠️ 전체 탭 클릭 실패 (무시됨): {e}")

        
        review_divs = []
        prev_count = 0
        same_count_tries = 0
        max_same_count_tries = 5

        while True:
            try:
                review_divs = self.driver.find_elements(By.CSS_SELECTOR, "div.hundred_list")
                logger.info(f"현재 리뷰 수: {len(review_divs)}")

                # 종료 조건 1: 리뷰 수 충분
                if len(review_divs) >=self.min_reviews:
                    logger.info("리뷰 최소 개수 도달")
                    break

                # 종료 조건 2: 리뷰 수가 더 이상 늘지 않음
                if len(review_divs) == prev_count:
                    same_count_tries += 1
                    if same_count_tries >= max_same_count_tries:
                        logger.warning("더 이상 리뷰 수 증가 없음. 중단.")
                        break
                else:
                    same_count_tries = 0
                    prev_count = len(review_divs)

                # 더보기 클릭
                more_button = self.driver.find_element(By.XPATH, '//a[contains(@href, "fn_CommunityReviewMore")]')
                self.driver.execute_script("arguments[0].click();", more_button)
                time.sleep(2.5) 

            except StaleElementReferenceException:
                logger.warning("StaleElement 예외 발생. 재시도 중...")
                time.sleep(1)
                continue

            except Exception as e:
                logger.error(f"예외 발생: {e}")
                break

        review_divs = self.driver.find_elements(By.CSS_SELECTOR, "div.hundred_list")

        for div in review_divs:
            try:
                # 별점 개수 세기 (on된 별 이미지만 카운트)
                stars = div.find_elements(By.CSS_SELECTOR, "div.HL_star img")
                rating = sum(1 for star in stars if "icon_star_on" in star.get_attribute("src"))

                text_span = div.find_element(By.CSS_SELECTOR, 'span[id^="spnPaper"]:not([style*="display:none"])')
                text = text_span.text.strip()

                # 날짜
                date_span = div.find_element(By.CSS_SELECTOR, "div.left span:nth-of-type(1)")
                date = date_span.text.strip()

                self.reviews.append({
                    "별점": rating,
                    "날짜": date,
                    "리뷰": text
                })

            except Exception as e:
                continue

        self.driver.quit()


    def save_to_database(self):
        df = pd.DataFrame(self.reviews)
        path = os.path.join(self.output_dir, "reviews_aladin.csv")
        df.to_csv(path, index=False, encoding="utf-8-sig")
        logger.info(f"{len(df)}개 리뷰 저장 완료: {path}")
