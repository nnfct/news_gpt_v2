import smtplib
import json
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from core.config import EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD, SUBSCRIBERS_FILE
from services.openai_service import generate_weekly_insight
from services.deepsearch_service import fetch_tech_articles, fetch_global_tech_articles

logger = logging.getLogger(__name__)

def load_subscribers():
    """구독자 목록 로드"""
    try:
        if os.path.exists(SUBSCRIBERS_FILE):
            with open(SUBSCRIBERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"구독자 로드 오류: {e}")
        return []

def save_subscribers(subscribers):
    """구독자 목록 저장"""
    try:
        with open(SUBSCRIBERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(subscribers, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"구독자 저장 오류: {e}")
        return False

async def send_email(to_email: str, subject: str, content: str):
    """이메일 발송 (HTML 형식)"""
    if not EMAIL_USER or not EMAIL_PASSWORD:
        logger.error("이메일 설정이 비어 있습니다. .env 파일을 확인하세요.")
        return False
    
    try:
        # 이메일 메시지 생성
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # HTML 본문 추가
        msg.attach(MIMEText(content, 'html'))
        
        # SMTP 서버 연결 및 발송
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()  # TLS 암호화
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"✅ 이메일 발송 성공: {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ 이메일 발송 실패 ({to_email}): {e}", exc_info=True)
        return False

async def get_weekly_keywords_data():
    """주간 키워드 데이터 수집"""
    from services.openai_service import extract_keywords_with_gpt, extract_global_keywords_with_gpt
    try:
        # 현재 주차 키워드 가져오기
        start_date = "2025-07-14"
        end_date = "2025-07-21"
        
        # 국내 키워드
        domestic_articles = await fetch_tech_articles(start_date, end_date)
        domestic_keywords = await extract_keywords_with_gpt(domestic_articles)
        
        # 해외 키워드
        global_articles = await fetch_global_tech_articles(start_date, end_date)
        global_keywords = await extract_global_keywords_with_gpt(global_articles)
        
        return {
            "domestic_keywords": domestic_keywords[:5],
            "global_keywords": global_keywords[:5],
            "period": f"{start_date} ~ {end_date}"
        }
    except Exception as e:
        logger.error(f"키워드 데이터 수집 오류: {e}")
        return {
            "domestic_keywords": [
                {"keyword": "인공지능", "count": 25, "rank": 1, "reason": "오류로 인한 샘플 데이터"},
                {"keyword": "반도체", "count": 20, "rank": 2, "reason": "오류로 인한 샘플 데이터"}
            ],
            "global_keywords": [
                {"keyword": "AI Technology", "count": 30, "rank": 1, "reason": "오류로 인한 샘플 데이터"},
                {"keyword": "Innovation", "count": 25, "rank": 2, "reason": "오류로 인한 샘플 데이터"}
            ],
            "period": "2025-07-14 ~ 2025-07-21"
        } 