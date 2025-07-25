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

#### 2. 전처리/FE: 각 크롤링 csv파일에 대해 진행한 결과 설명

#### 3. 비교분석: 결과에 대한 시각화 그래프 & 설명
