from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from konlpy.tag import Okt
import re

# Selenium을 이용한 기사 정보 추출 함수
def extract_article_info(article_url: str):   
    # Selenium WebDriver 설정
    options = Options()
    options.add_argument('headless')  # 브라우저 창 띄우지 않도록 설정
    options.add_argument("disable-gpu")
    prefs = {
        'profile.default_content_setting_values': {
            'images': 2,
            'stylesheet': 2,
            'font': 2,
        }
    }
    options.add_experimental_option('prefs', prefs)
    
    driver = webdriver.Chrome(options=options)
    driver.get(article_url)

    # 기사 제목 추출
    try:
        title = driver.find_element(By.CSS_SELECTOR, 'div.ArticleHead_article_head_title__YUNFf h2.ArticleHead_article_title__qh8GV').text
        title = re.sub(r'\[[^\]]*\]', '', title).strip()
    except Exception as e:
        title = ''
    
    # 기사 본문 추출
    try:
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        article_div = soup.find('div', class_='_article_content')

        # 이미지 설명 및 관련 요소 제거
        for span in article_div.find_all('span', class_='end_photo_org'):
            span.decompose()

        # 전체 텍스트 추출 후 줄 단위로 분리
        raw_text = article_div.get_text(separator='\n', strip=True)
        lines = raw_text.split('\n')

        cleaned_lines = []
        for line in lines:
            if '@' in line or 'YTN star' in line or 'OSEN DB' in line: # 특정 표현(@, ...)이 포함된 문장 제거
                continue
            line = line.strip()
            if not line:
                continue
            # '언론사 OOO 기자' 패턴 제거
            line = re.sub(r'[\[\(].*?기자.*?[\]\)]\s*', '', line)
            # '사진=...' 패턴 제거
            line = re.sub(r'[\[\(]?\s*사진(?:\s*출처)?\s*(?:=\s*)?.*', '', line)
            cleaned_lines.append(line)

        # 문단을 공백으로 연결
        content = ' '.join(cleaned_lines)

    except Exception:
        content = ''
        
    # 공감(전체) 이모티콘 개수 및 '놀랐어요', '슬퍼요' 이모티콘 개수
    surprise_count = 0
    sad_count = 0
    total_reactions = 0

    try:
        reaction_buttons = driver.find_elements(By.CSS_SELECTOR, 'ul.LikeitReactionList_comp_likeit_reaction_list__8LiHV li')
        
        # 각각 이모티콘 가져오기
        for button in reaction_buttons:
            try:
                label = button.find_element(By.CSS_SELECTOR, 'span.LikeitReactionList_text__EwbbK').text
                count_text = button.find_element(By.CSS_SELECTOR, 'em.LikeitReactionList_count__ys4Cl').text.replace(',', '')
                count = int(count_text)

                total_reactions += count

                if label == '놀랐어요':
                    surprise_count = count
                elif label == '슬퍼요':
                    sad_count = count
            except Exception:
                continue
    except Exception:
        pass

    # 비율 계산
    if total_reactions > 0:
        emotion_ratio = (surprise_count + sad_count) / total_reactions
    else:
        emotion_ratio = 0

    # 정보 반환
    driver.quit()
    return title, content, emotion_ratio


okt = Okt()

# 기사 제목과 본문을 받아 feature 추출
def extract_features(title: str, content: str) -> dict:
    title_text = title.strip()

    # 제목에 ' 또는 " 포함 여부
    quotation = int("'" in title_text or '"' in title_text)
    
    # 제목에 ♥ 포함 여부
    has_heart = int('♥' in title_text)

    # 제목에 .., ..., …, ‥ 포함 여부
    has_ellipsis = int('..' in title_text or '...' in title_text or '…' in title_text or '‥' in title_text)

    # 제목에 !, ? 포함 여부
    has_punctuation = int('!' in title_text or '?' in title_text)

    # 제목에 있지만 본문에 없는 키워드 비율 (명사, 형용사, 부사)
    title_tokens = okt.pos(title_text, norm=True) # , stem=True

    # 필터링: 명사, 형용사, 부사
    valid_pos = ['Noun', 'Adjective', 'Adverb']
    title_keywords = set([word for word, pos in title_tokens if pos in valid_pos])

    unseen_keywords = [word for word in title_keywords if word not in content]

    if len(title_keywords) == 0:
        unmatched_keyword_ratio = 0.0
    else:
        unmatched_keyword_ratio = round(len(unseen_keywords) / len(title_keywords), 3)
    
    return {
        'quotation': quotation,
        'has_heart': has_heart,
        'has_ellipsis': has_ellipsis,
        'has_punctuation': has_punctuation,
        'unmatched_keyword_ratio': unmatched_keyword_ratio
    }