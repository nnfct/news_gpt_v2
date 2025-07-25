import logging
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from core.schemas import SubscriptionRequest, EmailInsightRequest
from services.email_service import load_subscribers, save_subscribers, send_email, get_weekly_keywords_data
from services.openai_service import generate_weekly_insight
from core.config import EMAIL_USER, EMAIL_PASSWORD

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/subscribe")
async def subscribe_email_endpoint(subscription: SubscriptionRequest):
    """이메일 구독 API"""
    try:
        email = subscription.email
        subscribers = load_subscribers()
        
        for subscriber in subscribers:
            if subscriber.get("email") == email:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "이미 구독된 이메일입니다."}
                )
        
        from datetime import datetime
        new_subscriber = {
            "email": email,
            "subscribed_at": datetime.now().isoformat(),
            "active": True
        }
        
        subscribers.append(new_subscriber)
        
        if save_subscribers(subscribers):
            logger.info(f"✅ 새 구독자 추가: {email}")
            return JSONResponse(
                status_code=200,
                content={
                    "message": "구독이 완료되었습니다!",
                    "email": email
                }
            )
        else:
            raise HTTPException(status_code=500, detail="구독 저장 중 오류가 발생했습니다.")
            
    except Exception as e:
        logger.error(f"❌ 구독 오류: {e}")
        raise HTTPException(status_code=500, detail=f"구독 처리 중 오류: {str(e)}")

@router.get("/subscribers")
async def get_subscribers():
    """구독자 목록 조회 API"""
    try:
        subscribers = load_subscribers()
        return JSONResponse(
            status_code=200,
            content=subscribers
        )
    except Exception as e:
        logger.error(f"❌ 구독자 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"구독자 목록 조회 중 오류: {str(e)}")

@router.post("/send-insights")
async def send_weekly_insights(request: EmailInsightRequest):
    """주간 인사이트 이메일 발송 API (수동 발송용)"""
    try:
        if not EMAIL_USER or not EMAIL_PASSWORD:
            return JSONResponse(
                status_code=500,
                content={
                    "error": "이메일 설정이 필요합니다",
                    "detail": ".env 파일에 EMAIL_USER와 EMAIL_PASSWORD를 설정해주세요.",
                    "instruction": "Gmail 앱 비밀번호 설정 후 .env 파일을 업데이트하세요."
                }
            )
        
        email = request.email
        keywords_data = await get_weekly_keywords_data()
        insight_content = await generate_weekly_insight(keywords_data)
        success = await send_email(email, "📊 주간 AI 뉴스 인사이트", insight_content)
        
        if success:
            return JSONResponse(
                status_code=200,
                content={"message": f"인사이트가 {email}로 발송되었습니다."}
            )
        else:
            raise HTTPException(status_code=500, detail="이메일 발송 실패")
            
    except Exception as e:
        logger.error(f"❌ 인사이트 발송 오류: {e}")
        raise HTTPException(status_code=500, detail=f"발송 중 오류: {str(e)}")

@router.post("/send-to-all-subscribers")
async def send_to_all_subscribers():
    """모든 구독자에게 주간 인사이트 발송"""
    try:
        subscribers = load_subscribers()
        active_subscribers = [s for s in subscribers if s.get("active", True)]
        
        if not active_subscribers:
            return JSONResponse(
                status_code=200,
                content={"message": "활성 구독자가 없습니다.", "sent_count": 0}
            )
        
        keywords_data = await get_weekly_keywords_data()
        insight_content = await generate_weekly_insight(keywords_data)
        
        sent_count = 0
        failed_count = 0
        
        for subscriber in active_subscribers:
            email = subscriber.get("email")
            try:
                success = await send_email(email, "📊 주간 AI 뉴스 인사이트", insight_content)
                if success:
                    sent_count += 1
                    logger.info(f"✅ 발송 성공: {email}")
                else:
                    failed_count += 1
                    logger.warning(f"❌ 발송 실패: {email}")
                    
                await asyncio.sleep(1)
                
            except Exception as e:
                failed_count += 1
                logger.error(f"❌ {email} 발송 오류: {e}")
        
        return JSONResponse(
            status_code=200,
            content={
                "message": f"발송 완료: 성공 {sent_count}건, 실패 {failed_count}건",
                "sent_count": sent_count,
                "failed_count": failed_count,
                "total_subscribers": len(active_subscribers)
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 전체 발송 오류: {e}")
        raise HTTPException(status_code=500, detail=f"전체 발송 중 오류: {str(e)}") 