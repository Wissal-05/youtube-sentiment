from typing import Dict, List

from pydantic import BaseModel, Field, field_validator

MAX_BATCH = 1000
MAX_CHARS = 5000


class BatchRequest(BaseModel):
    comments: List[str] = Field(..., min_length=1, max_length=MAX_BATCH)

    @field_validator("comments")
    @classmethod
    def check_comments(cls, v):
        v = [c[:MAX_CHARS] for c in v]   # tronque les textes trop longs
        if not any(c.strip() for c in v):
            raise ValueError("Tous les commentaires sont vides")
        return v


class Prediction(BaseModel):
    text: str
    label: int
    sentiment: str
    confidence: float
    probabilities: Dict[str, float]


class Statistics(BaseModel):
    total: int
    counts: Dict[str, int]
    percentages: Dict[str, float]
    average_confidence: float
    dominant_sentiment: str


class BatchResponse(BaseModel):
    predictions: List[Prediction]
    statistics: Statistics
    processing_time_ms: float


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    n_features: int | None = None
    version: str