def get_sample_keywords_by_date(start_date: str, end_date: str):
    """날짜에 따른 샘플 키워드 반환 (reason 포함)"""
    default_reason = "API 호출 실패로 인한 샘플 데이터"

    if "07-01" in start_date:
        return [
            {"keyword": "전기차", "count": 250, "rank": 1, "reason": "최근 전기차 판매 증가 및 정책 지원"},
            {"keyword": "배터리", "count": 230, "rank": 2, "reason": "차세대 배터리 기술 개발 경쟁 심화"},
            {"keyword": "충전인프라", "count": 210, "rank": 3, "reason": "전기차 충전 인프라 확충 요구 증대"},
            {"keyword": "자율주행", "count": 190, "rank": 4, "reason": "자율주행 기술 상용화 논의 활발"},
            {"keyword": "테슬라", "count": 170, "rank": 5, "reason": "테슬라 신모델 출시 및 시장 영향력"},
        ]
    elif "07-06" in start_date:
        return [
            {"keyword": "메타버스", "count": 250, "rank": 1, "reason": "가상현실 기술의 발전과 엔터테인먼트 산업 적용"},
            {"keyword": "VR", "count": 230, "rank": 2, "reason": "VR 기기 보급 확대 및 콘텐츠 다양화"},
            {"keyword": "가상현실", "count": 210, "rank": 3, "reason": "가상현실 기술의 산업 활용 분야 확대"},
            {"keyword": "AR", "count": 190, "rank": 4, "reason": "증강현실 기술의 일상생활 적용"},
            {"keyword": "NFT", "count": 170, "rank": 5, "reason": "디지털 자산 시장의 새로운 트렌드"},
        ]
    elif "07-14" in start_date:
        return [
            {"keyword": "인공지능", "count": 250, "rank": 1, "reason": "AI 기술의 범용화 및 다양한 산업 적용"},
            {"keyword": "AI", "count": 230, "rank": 2, "reason": "AI 모델 고도화 및 학습 데이터 중요성"},
            {"keyword": "ChatGPT", "count": 210, "rank": 3, "reason": "대화형 AI의 발전과 서비스 확산"},
            {"keyword": "머신러닝", "count": 190, "rank": 4, "reason": "데이터 기반의 예측 및 분석 능력 향상"},
            {"keyword": "딥러닝", "count": 170, "rank": 5, "reason": "복잡한 문제 해결을 위한 딥러닝 알고리즘 활용"},
        ]
    else:
        return [
            {"keyword": "기술", "count": 250, "rank": 1, "reason": default_reason},
            {"keyword": "혁신", "count": 230, "rank": 2, "reason": default_reason},
            {"keyword": "디지털", "count": 210, "rank": 3, "reason": default_reason},
            {"keyword": "정보", "count": 190, "rank": 4, "reason": default_reason},
            {"keyword": "시스템", "count": 170, "rank": 5, "reason": default_reason}
        ]

def get_global_sample_keywords_by_date(start_date: str, end_date: str):
    """해외 주간별 샘플 키워드 반환"""
    global_keywords_map = {
        "2025-07-01": ["AI Revolution", "Quantum Computing", "Green Tech"],
        "2025-07-06": ["ChatGPT-5", "Tesla Robotics", "Web3"],
        "2025-07-14": ["Neural Chips", "Space Tech", "Bio Computing"]
    }
    
    for date_key, keywords in global_keywords_map.items():
        if start_date >= date_key:
            return keywords
    
    return ["AI Technology", "Innovation", "Future Tech"] 