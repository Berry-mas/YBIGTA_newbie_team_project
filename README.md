# YBIGTA_newbie_team_project

연세대학교 YBIGTA 27기 여름방학 교육세션 9조 팀플 과제를 위한 repository입니다.

## 팀원 구성 및 자기소개

| 박준서                                                           | 안시연                                                           | 이지민                                                           |
| ---------------------------------------------------------------- | ---------------------------------------------------------------- | ---------------------------------------------------------------- |
| ![박준서](https://avatars.githubusercontent.com/u/106491547?v=4) | ![안시연](https://avatars.githubusercontent.com/u/106491548?v=4) | ![이지민](https://avatars.githubusercontent.com/u/106491549?v=4) |
| [GitHub](https://github.com/Berry-mas)                           | [GitHub](https://github.com/WalkingTiRaMiSu)                     | [GitHub](https://github.com/jimiracle)                           |

#### 박준서

- MBTI : ESFJ
- 학과 : 정치외교학과/응용통계학과
- 취미 : 야구 관람 (LG TWINS 팬입니다!)

#### 안시연

- MBTI : INFP
- 학과 : 건축공학과
- 취미 : 게임하기

#### 이지민

- MBTI : ISTJ
- 학과 : 응용통계학과
- 취미 : 잠자기

### **Git 과제**

![alt text](github/review_and_merged.png) ![alt text](github/branch_protection.png) ![alt text](github/push_rejected.png)

### **크롤링한 리뷰 데이터 소개**

#### 1. 교보문고 (소년이 온다)

- 사이트 링크 : https://product.kyobobook.co.kr/detail/S000000610612
- 데이터 개수 : 501개
- 데이터 형식
  - reviews_kyobo.csv
  - 파일 형식: CSV (쉼표로 구분된 값)
  - 컬럼 구성
    | 컬럼명 | 설명 |
    |--------|--------------------|
    | text | 리뷰 본문 |
    | date | 리뷰 작성일 (yyyy.mm.dd) |
    | score | 리뷰 평점 (예: 10.0) |

#### 2. 알라딘 (소년이 온다)

- 사이트 링크 : https://www.aladin.co.kr/shop/wproduct.aspx?ItemId=40869703
- 데이터 개수 : 590개
- 데이터 형식
  - reviews_aladin.csv
  - 파일 형식: CSV (쉼표로 구분된 값)
  - 컬럼 구성
    | 컬럼명 | 설명 |
    |--------|--------------------|
    | 리뷰 | 리뷰 본문 |
    | 날짜 | 리뷰 작성일 (yyyy-mm-dd) |
    | 별점 | 리뷰 평점 (예: 5) |

#### 3. yes24 (소년이 온다)

- 사이트 링크 : https://www.yes24.com/product/goods/13137546
- 데이터 개수 : 1021개
- 데이터 형식
  - reviews_yes24.csv
  - 파일 형식: CSV (쉼표로 구분된 값)
  - 컬럼 구성
    | 컬럼명 | 설명 |
    |--------|--------------------|
    | review | 리뷰 본문 |
    | day | 리뷰 작성일 (yyyy-mm-dd)s |
    | rate | 리뷰 평점 (예: 평점10점) |
    | Unnamed: 0 | 인덱스 열 |

### **코드 실행 방법**

#### 1. Web

YBIGTA_newbie_team_project\app에서
python main.py 을 터미널/Powershell에 입력해주세요.
만약 module을 찾을 수 없다면 같은 위치에서

- Mac/Linux : export PYTHONPATH="../"
- Windows(Powershell 기준) : $env:PYTHONPATH = "../"
  를 입력한 후 python main.py를 입력해주세요.

이후 브라우저에서 http://localhost:8000/docs로 입력하면 api들을 실행할 수 있습니다.

#### 2. 크롤링

YBIGTA_newbie_team_project\review_analysis\crawling에서
python main.py -o ../../database --all을 터미널/Powershell에 입력해주세요.
만약 module을 찾을 수 없다면 같은 위치에서

- Mac/Linux : export PYTHONPATH="../.."
- Windows(Powershell 기준) : $env:PYTHONPATH = "../.."
  를 입력한 후 python main.py -o ../../database --all 을 입력해주세요.

#### 3. EDA/FE

YBIGTA_newbie_team_project\review_analysis\preprocessing에서
python main.py -o ../../database --all을 터미널/Powershell에 입력해주세요.
만약 module을 찾을 수 없다면 같은 위치에서

- Mac/Linux : export PYTHONPATH="../.."
- Windows(Powershell 기준) : $env:PYTHONPATH = "../.."
  를 입력한 후 python main.py -o ../../database --all 을 입력해주세요.

### **EDA&FE, 시각화 설명**

#### 1. EDA: 개별 사이트에 대한 시각화 그래프 & 설명

<details>
<summary> kyobo - EDA/FE, 시각화 과제</summary>

### Kyobo EDA

1. 별점 분포
   ![alt text](review_analysis/plots/kyobo_rating_dist.png)

- 분석 내용: 대부분의 리뷰가 **10점(만점)**을 부여하고 있음.

- 특징: 분포의 한쪽에 몰림이 심함. 극단적으로 높은 점수 쏠림 현상.

- 이상치: 3~6점대의 낮은 별점도 소수 존재하나, 전체에서 차지하는 비율은 매우 적음.

- 해석: 해당 도서에 대한 감정적 반응이 매우 강하고 긍정적임. "의무적으로라도 남긴다"는 성격의 리뷰보다는, 책의 메시지에 공감하여 자발적으로 남긴 후기들이 많을 가능성이 큼.

2. 전체 리뷰 길이 분포
   ![alt text](review_analysis/plots/kyobo_text_length_dist.png)

- 분석 내용: 대부분의 리뷰가 20~80자 사이에 집중됨.

- 특징: 길이가 매우 짧거나 매우 긴 리뷰는 극소수에 해당하며, 오른쪽 꼬리가 긴 우측 비대칭 분포를 보임.

- 이상치: 300자 이상의 리뷰는 극히 드물며, 에세이 수준의 심층 리뷰일 가능성이 있음.

- 해석: 독자들은 짧지만 진심을 담은 감상 중심의 리뷰를 남기며, 극소수는 책에 대한 감정을 길게 서술함.

3. 너무 짧은 리뷰 길이 분포 (10자 이하)
   ![alt text](review_analysis/plots/kyobo_short_review_dist.png)

- 분석 내용: 10자 이하의 짧은 리뷰는 전체 중 매우 적은 수.

- 특징: **10자에 가까운 리뷰(9~10자)**가 상대적으로 많고, 그보다 짧은 리뷰는 거의 없음.

- 이상치: 5자 이하 리뷰는 소수이며, 자동 생성 또는 비정상 입력 가능성 있음.

- 해석: 대부분 사용자들이 최소한의 감정을 표현하려는 경향이 있으며, 완전히 무의미한 리뷰는 적음.

4. 날짜별 리뷰 수 변화

![alt text](review_analysis/plots/kyobo_review_by_date.png)

- 분석 내용: 2023년까지는 거의 리뷰가 없고, 2024년 후반~2025년에 급증함.

- 특징: 최근 특정 시점 이후 리뷰가 집중적으로 생성됨.

- 이상치: 2025년 일부 날짜에 급격하게 리뷰 수가 증가한 날들이 존재함.

- 해석: 책의 재조명, SNS나 유튜브 등 외부 영향(콘텐츠, 사회적 이슈 등)에 의해 관심이 급증했을 가능성 있음.
</details>

<details>
<summary> aladin - EDA/FE, 시각화 과제</summary>

### Aladin EDA

1. 별점 분석
   ![alt text](review_analysis/plots/aladin-score-histogram.png)
   ![alt text](review_analysis/plots/aladin-score-piechart.png)

- 별점 5점이 전체의 약 88% 이상을 차지하며 매우 집중되어있고 그 외 점수(1~4)는 극소수에 불과하다.
- 분포가 극단적으로 한쪽으로 쏠려있다.

2. 텍스트 길이 분포

![alt text](review_analysis/plots/aladin-textlen-historgram.png)

- 대부분의 리뷰는 20자 ~ 150자 내외에 분포하고 드물게 400자 이상의 매우 긴 리뷰도 존재한다.
- 분포가 극단적으로 한쪽으로 쏠려있다.

3. 날짜별 리뷰 수

![alt text](review_analysis/plots/aladin-datereview.png)

- 2014~2021년까지 꾸준히 리뷰 존재
- 2025년대 이후로 급증

</details>

#### 2. 전처리/FE: 각 크롤링 csv파일에 대해 진행한 결과 설명

<details> 
<summary> kyobo - Preprocessing / FE </summary>

### kyobo Preprocessing / FE

각 크롤링된 CSV 파일에 대해 진행한 전처리 및 피처 엔지니어링 과정을 설명합니다.  
모든 단계는 모델 입력을 위한 정제 및 벡터화를 목표로 수행되었습니다.

---

#### 1. 결측치 처리

- `score`, `text`, `date` 컬럼에서 결측값이 존재하는 행은 모두 제거하였습니다.
- 분석 및 벡터화 과정에서 오류를 유발하거나 무의미한 데이터를 제거함으로써 데이터 정합성을 확보했습니다.

---

#### 2. 이상치 제거

- 리뷰 별점은 원래 1~5 범위였으며, 분석의 일관성을 위해 2배를 곱해 0~10 스케일로 변환하였습니다.
- 이후 다음 조건에 해당하는 데이터를 이상치로 간주하고 제거하였습니다:
  - 별점이 0 미만 또는 10 초과인 경우
  - 리뷰 텍스트의 길이가 5자 미만이거나 1000자 초과인 경우
- 이러한 이상치는 시스템 오류, 자동 생성 리뷰, 의도치 않은 입력 등으로 발생했을 가능성이 있어 제거 대상이 되었습니다.

---

#### 3. 텍스트 데이터 전처리

- 리뷰 텍스트에서 한글, 숫자, 공백 외의 특수문자를 모두 제거하였습니다.
- 정규표현식을 이용해 불필요한 기호, 이모지, HTML 태그 등을 제거하여 텍스트 분석 품질을 향상시켰습니다.
- 전처리된 텍스트는 `cleaned_text` 컬럼으로 저장하였습니다.

---

#### 4. 파생변수 생성

- 리뷰 작성 날짜(`date`)로부터 요일 정보를 파생하여 `weekday` 컬럼을 생성하였습니다.
- 이 파생변수는 주말/평일 리뷰 작성 패턴, 소비자 반응 시간대 분석 등에 활용될 수 있습니다.
- 예: Monday, Tuesday, ..., Sunday

---

#### 5. 텍스트 벡터화 (TF-IDF)

- `cleaned_text` 컬럼을 기반으로 TF-IDF(Term Frequency - Inverse Document Frequency) 벡터화를 수행하였습니다.
- 가장 많이 등장하고 동시에 정보량이 높은 상위 100개의 단어를 기준으로 벡터화하였으며,  
  각 문서는 `tfidf_0 ~ tfidf_99`의 100차원 수치 벡터로 표현됩니다.
- 이 과정은 이후 군집화, 감성 분석, 분류 모델링 등에 사용될 수 있는 정량적 표현을 제공하기 위한 것입니다.
</details>

<details> 
<summary> aladin - Preprocessing / FE </summary>

### Aladin Preprocessing / FE

1. 결측치 처리

- score, text, date 컬럼에서 결측값이 있는 행은 모두 제거

2. 이상치 제거

- 원래 별점이 1 ~ 5 사이였으므로 2배하여 0~10 스케일로 변환하였음
- 범위를 벗어난 별점 점수(<0 또는 >10)는 제거
- 리뷰 텍스트의 길이가 5자 미만 혹은 1000자 초과인 경우 이상치로 간주하여 제거

3. 텍스트 전처리

- 리뷰 텍스트에서 한글, 숫자, 공백 외의 특수문자 제거

4.  파생변수 생성

- 요일(Weekday) : 리뷰가 작성된 날짜에서 요일(Monday, Tuesday, …) 파생, 소비자 행동 패턴(주말/평일)에 따른 분석 가능성 확보

5. 텍스트 벡터화 (TF-IDF)

- cleaned_text 열을 기반으로, 상위 100개의 단어에 대해 TF-IDF 벡터 생성
- 각 문장은 tfidf_0 ~ tfidf_99로 이루어진 100차원 수치 벡터로 변환됨

</details>

#### 3. 비교분석: 결과에 대한 시각화 그래프 & 설명

<!-- [인터랙티브 리뷰 트렌드 차트 보기](review_analysis/plots/daily_review_trends_interactive.html)

<iframe src="review_analysis/plots/daily_review_trends_interactive.html"
        width="100%" height="600px" frameborder="0"></iframe> -->
