from pydantic import BaseModel
from typing import List, Optional

class SubscriptionRequest(BaseModel):
    email: str

class EmailInsightRequest(BaseModel):
    email: str

class JobAnalysisRequest(BaseModel):
    query: str
    selected_keyword: Optional[str] = None
    selected_keyword_reason: Optional[str] = None

class IndustryKeywordAnalysisRequest(BaseModel):
    industry_perspective: str
    target_keyword: str

class TrendRequest(BaseModel):
    keyword: str
    country: str
    headlines: List[str] 