from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from data_extraction import extract_article_info, extract_features
from model_loader import summarize, generate, clickbait_model, clean_title, remove_duplicate_words
import pandas as pd
import re


app = Flask(__name__)
CORS(app)
    

@app.route('/')
def index():
    return "Loading..."


@app.route('/process', methods=['POST'])
def process_news():
    data = request.get_json()
    html = data['html']
    base_url = data['url']

    soup = BeautifulSoup(html, 'html.parser')

    # 기사 링크들 추출
    article_tags = soup.select('a.NewsItem_link_news__tD7x3')
    article_urls = [tag['href'] for tag in article_tags]

    results = []

    def process_single_article(url):
        try:
            title, content, emotion_ratio = extract_article_info(url)

            # Feature 추출
            features = extract_features(title, content)
            features['emotion_ratio'] = emotion_ratio

            feature_df = pd.DataFrame([{
                'quotation': features['quotation'],
                'has_heart': features['has_heart'],
                'has_ellipsis': features['has_ellipsis'],
                'has_punctuation': features['has_punctuation'],
                'unmatched_keyword_ratio': features['unmatched_keyword_ratio'],
                'emotion_ratio': features['emotion_ratio']
            }])

            # 클릭베이트 탐지
            is_clickbait = clickbait_model.predict(feature_df)[0]
            
            if is_clickbait == 1:
                return None

            # 요약 및 제목 생성
            summ_content = summarize(content)
            new_title = generate(summ_content)
            
            # 생성 제목 후처리
            if len(new_title) > 48:
                new_title = generate(summ_content)
            
            # <s>, </s>, <pad> 및 중복 단어 제거
            new_title = clean_title(new_title)
            new_title = remove_duplicate_words(new_title)

            return {
                "url": url,
                "new_title": new_title,
            }
        except Exception as e:
            return None
    
    with ThreadPoolExecutor(max_workers=5) as executor: # 스레드 5개 사용
        futures = {executor.submit(process_single_article, url): idx for idx, url in enumerate(article_urls)}
        results_with_index = []

        for future in as_completed(futures):
            result = future.result()
            if result:
                idx = futures[future]
                results_with_index.append((idx, result))

        # 정렬하여 순서 유지
        results = [r for _, r in sorted(results_with_index, key=lambda x: x[0])]
                        
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, port=5000)