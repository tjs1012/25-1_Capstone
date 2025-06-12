import os
import re
import torch
import pickle
from transformers import PreTrainedTokenizerFast, BartForConditionalGeneration
from article_generate import KoBARTConditionalGeneration

# Clickbait 탐지 모델
clickbait_detect_model_path = os.path.join(os.path.dirname(__file__), 'models', 'clickbait_detect_model.pkl')
with open(clickbait_detect_model_path, 'rb') as f:
    clickbait_model = pickle.load(f)


# 1차 모델(기사 본문 요약)
summ_model_path = os.path.join(os.path.dirname(__file__), 'models', 'kobart_summarization_model')

# 모델과 토크나이저 불러오기
summ_model_tokenizer = PreTrainedTokenizerFast.from_pretrained(summ_model_path)
summ_model = BartForConditionalGeneration.from_pretrained(summ_model_path)

def summarize(text):
    # 입력 텍스트 토크나이즈 및 전처리
    input_ids = summ_model_tokenizer.encode(
        text,
        max_length=1024,
        truncation=True
    )
    input_ids = [summ_model_tokenizer.bos_token_id] + input_ids + [summ_model_tokenizer.eos_token_id]
    input_ids = torch.tensor([input_ids])

    # 요약 생성
    summary_ids = summ_model.generate(
        input_ids=input_ids,
        bos_token_id=summ_model.config.bos_token_id,
        eos_token_id=summ_model.config.eos_token_id,
        length_penalty=0.2,
        max_length=64,
        min_length=25,
        num_beams=4
    )
    return summ_model_tokenizer.decode(summary_ids[0], skip_special_tokens=True)


# 2차 모델(기사 제목 생성)
generate_model_path = os.path.join(os.path.dirname(__file__), 'models', 'generate_model')

generate_model_tokenizer = PreTrainedTokenizerFast.from_pretrained(generate_model_path)
generate_model_model = BartForConditionalGeneration.from_pretrained(generate_model_path)

generate_model = KoBARTConditionalGeneration({
    "lr": 5e-6,
    "warmup_ratio": 0.1,
    "batch_size": 32,
    "max_length": 128,
    "max_epochs": 15
}, tokenizer=generate_model_tokenizer,
   model=generate_model_model,
   train_data_len=4883)

def generate(summ_text):
    result = generate_model.test(summ_text)
    return result


# 기사 제목 생성 모델 후처리
def clean_title(title):
                title = title.replace("</s>", "").replace("<s>", "")
                title = title.replace("<pad>", "")
                return title

def remove_duplicate_words(text):
    words = re.findall(r'\b\w+\b', text)
    seen = set()
    result = []
    for word in words:
        if word not in seen:
            result.append(word)
            seen.add(word)
    return ' '.join(result)