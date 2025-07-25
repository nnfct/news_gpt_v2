from fastapi import APIRouter

from api.v1 import api_v1_router

router = APIRouter()

router.include_router(api_v1_router.router, prefix="/api") 