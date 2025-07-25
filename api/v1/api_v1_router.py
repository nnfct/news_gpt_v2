from fastapi import APIRouter

from api.v1.endpoints import keywords, analysis, chat, subscription

router = APIRouter()

router.include_router(keywords.router, prefix="/v1", tags=["Keywords"])
router.include_router(analysis.router, prefix="/v1", tags=["Analysis"])
router.include_router(chat.router, prefix="/v1", tags=["Chat"])
router.include_router(subscription.router, prefix="/v1", tags=["Subscription"]) 