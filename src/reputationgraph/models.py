from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


class Mention(BaseModel):
    id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=500)
    text: str = Field(min_length=1, max_length=20_000)
    source: str = Field(min_length=1, max_length=200)
    url: HttpUrl
    published_at: datetime
    reach: int = Field(default=0, ge=0, le=1_000_000_000)
    tags: list[str] = Field(default_factory=list, max_length=30)

    @field_validator("published_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("published_at must include a timezone")
        return value.astimezone(UTC)


class AnalysisRequest(BaseModel):
    subject: str = Field(min_length=2, max_length=200)
    mentions: list[Mention] = Field(min_length=1, max_length=2_000)
    as_of: datetime | None = None


class ScoreComponents(BaseModel):
    negative_tone: float
    reach: float
    recency: float
    source_diversity: float
    corroboration: float


class Evidence(BaseModel):
    mention_id: str
    title: str
    source: str
    url: HttpUrl
    published_at: datetime


class Narrative(BaseModel):
    name: str
    mention_ids: list[str]
    sources: list[str]
    risk_score: float
    severity: Literal["low", "moderate", "high", "critical"]
    components: ScoreComponents
    explanation: list[str]
    evidence: list[Evidence]


class GraphNode(BaseModel):
    id: str
    label: str
    kind: Literal["subject", "entity", "narrative", "source"]


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: Literal["mentions", "publishes", "co-occurs", "concerns"]
    weight: int = 1


class AnalysisResult(BaseModel):
    subject: str
    generated_at: datetime
    mention_count: int
    overall_risk: float
    narratives: list[Narrative]
    nodes: list[GraphNode]
    edges: list[GraphEdge]
