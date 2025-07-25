import logging
from fastapi import APIRouter, HTTPException
from starlette.responses import JSONResponse

from core.schemas import JobAnalysisRequest, IndustryKeywordAnalysisRequest
from services.openai_service import get_job_industry_summary, generate_industry_based_answer, generate_comparison_answer

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/job-analysis")
async def analyze_job_industry(request: JobAnalysisRequest):
    user_job_role = request.query
    analysis_keyword = request.selected_keyword
    analysis_keyword_reason = request.selected_keyword_reason


    if not analysis_keyword:
        analysis_keyword = "인공지능"
        analysis_keyword_reason = "사용자가 선택하지 않아 기본값으로 설정됨"
        logger.warning(f"⚠️ analysis_keyword가 제공되지 않아 '{analysis_keyword}'를 기본값으로 사용합니다.")


    if not user_job_role:
        raise HTTPException(status_code=400, detail="분석할 직무/산업을 입력해야 합니다.")

    logger.info(f"📊 직무/산업 분석 요청: 관점='{user_job_role}', 대상 키워드='{analysis_keyword}'")

    try:
        summary = await get_job_industry_summary(user_job_role)


        # 2-1. 긍정적 분석 생성 (강화된 프롬프트 적용)
        positive_analysis_result = await generate_industry_based_answer(
            question=f"'{analysis_keyword}'에 대한 '{user_job_role}' 직무 관점에서의 긍정적 분석",
            keyword=analysis_keyword,
            industry=user_job_role,
            current_keywords=[analysis_keyword],
            reason=analysis_keyword_reason
        )

        # 2-2. 비판적 분석을 위한 프롬프트 구성 (긍정적 분석 결과 포함)
        critical_analysis_full_prompt = f"""
        다음은 '{analysis_keyword}'에 대한 '{user_job_role}' 직무 관점의 **긍정적 분석 결과**입니다:
        ---
        {positive_analysis_result}
        ---

        이 긍정적 분석 내용을 **참고**하되, 이와는 **다른 관점에서 비판적 분석**을 제공해주세요.
        '{user_job_role}' 직무 관점에서 '{analysis_keyword}' 키워드가 가질 수 있는 **잠재적 위험, 한계, 부정적인 측면, 또는 극복해야 할 과제** 등을 중심으로 심층적으로 설명해주세요.
        긍정적 분석과 **비슷한 분량**으로, 그리고 **유사한 상세 형식**으로 답변을 작성해주세요.
        """

        # generate_comparison_answer 함수 호출 시 새로 구성한 프롬프트 전달
        counter_analysis_result = await generate_comparison_answer(
            question=critical_analysis_full_prompt,
            keywords=[analysis_keyword],
            perspective_role=user_job_role,
            reason=analysis_keyword_reason
        )

        if not summary:
            logger.warning(f"⚠️ 직무/산업 요약 결과 없음 또는 오류 발생 for query: {user_job_role}")
            return JSONResponse(status_code=500, content={"error": "직무/산업 정보를 분석할 수 없습니다. 더 구체적인 질문을 해주세요."})

        logger.info(f"✅ 직무/산업 분석 완료. 요약 길이: {len(summary)}")
        return {
            "query": user_job_role,
            "summary": summary,
            "insight_analysis": positive_analysis_result,
            "counter_insight_analysis": counter_analysis_result,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"❌ 직무/산업 분석 엔드포인트 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"직무/산업 분석 중 서버 오류 발생: {str(e)}")

@router.post("/industry-analysis")
async def get_industry_analysis(request: IndustryKeywordAnalysisRequest):
    industry_perspective = request.industry_perspective
    target_keyword = request.target_keyword

    if not industry_perspective or not target_keyword:
        raise HTTPException(status_code=400, detail="분석 관점과 키워드를 모두 제공해야 합니다.")

    logger.info(f"📊 산업별/직무 관점 분석 요청: 관점='{industry_perspective}', 키워드='{target_keyword}'")

    try:
        main_completion_content = await generate_industry_based_answer(
            question=f"'{target_keyword}'에 대한 '{industry_perspective}' 직무/산업 관점에서의 긍정적 분석",
            keyword=target_keyword,
            industry=industry_perspective,
            current_keywords=[target_keyword]
        )

        counter_completion_content = await generate_comparison_answer(
            question=f"'{target_keyword}'에 대한 '{industry_perspective}' 직무/산업 관점에서의 비판적 분석",
            keywords=[target_keyword],
        )

        return {
            "analysis": main_completion_content,
            "counter_analysis": counter_completion_content
        }
    except Exception as e:
        logger.error(f"❌ 산업별/직무 관점 분석 엔드포인트 오류: {e}", exc_info=True)
        return {
            "analysis": f"분석을 생성하는 중 오류가 발생했습니다: {str(e)}",
            "counter_analysis": "반대 의견을 생성할 수 없습니다."
        } 