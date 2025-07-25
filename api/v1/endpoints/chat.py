import logging

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from core.schemas import TrendRequest
from services.openai_service import extract_keyword_and_industry, generate_industry_based_answer, get_current_weekly_keywords, generate_keyword_trend_answer, generate_comparison_answer, generate_contextual_answer, get_gpt_commentary

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/chat")
async def chat(request: Request):
    """산업별 키워드 분석 기반 동적 챗봇"""
    try:
        data = await request.json()
        question = data.get("question") or data.get("message") or ""
        if not question:
            return JSONResponse(content={"answer": "질문을 입력해주세요."})
        
        keyword_info = extract_keyword_and_industry(question)
        current_weekly_keywords = get_current_weekly_keywords() 

        answer = "답변을 생성할 수 없습니다."

        if keyword_info["type"] == "industry_analysis":
            answer = await generate_industry_based_answer( 
                question,
                keyword_info["keyword"],
                keyword_info["industry"],
                current_weekly_keywords,
                reason=keyword_info["reason"]
            )
        elif keyword_info["type"] == "keyword_trend":
            answer = await generate_keyword_trend_answer(question, keyword_info["keyword"])
        elif keyword_info["type"] == "comparison":
            answer = await generate_comparison_answer( 
                question,
                keyword_info["keywords"],
                perspective_role=keyword_info["industry"],
                reason=keyword_info["reason"]
            )
        else:
            answer = await generate_contextual_answer(question, current_weekly_keywords) 

        return JSONResponse(content={"answer": answer})
    except Exception as e:
        logger.error(f"/chat 오류: {e}", exc_info=True)
        return JSONResponse(content={
            "answer": "챗봇 서비스에 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        }, status_code=500)

@router.post("/gpt-commentary")
async def generate_commentary_endpoint(req: TrendRequest):
    """트렌드에 대한 AI 해설 생성"""
    try:
        commentary = await get_gpt_commentary(req)

        return JSONResponse(content={"comment": commentary})
    except Exception as e:
        logger.error(f"Error in /api/v1/gpt-commentary endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate commentary.") 