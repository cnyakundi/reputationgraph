from __future__ import annotations

import math
import re
from datetime import datetime

from reputationgraph.models import Mention, ScoreComponents

NEGATIVE_TERMS = {
    "breach", "complaint", "delay", "failure", "fraud", "investigation",
    "lawsuit", "misleading", "outage", "recall", "risk", "unsafe",
}
POSITIVE_TERMS = {
    "award", "improved", "innovation", "resolved", "safe", "success", "transparent",
}


def tone_score(mentions: list[Mention]) -> float:
    words = re.findall(r"[a-z]+", " ".join(f"{m.title} {m.text}" for m in mentions).lower())
    if not words:
        return 0.0
    negative = sum(word in NEGATIVE_TERMS for word in words)
    positive = sum(word in POSITIVE_TERMS for word in words)
    evidence = negative + positive
    if evidence == 0:
        return 25.0
    return max(0.0, min(100.0, 100 * negative / evidence))


def score(mentions: list[Mention], as_of: datetime) -> tuple[float, ScoreComponents, list[str]]:
    tone = tone_score(mentions)
    total_reach = sum(m.reach for m in mentions)
    reach = min(100.0, math.log10(total_reach + 1) / 6 * 100)
    newest_age = min(max(0.0, (as_of - m.published_at).total_seconds() / 86400) for m in mentions)
    recency = 100 * math.exp(-newest_age / 30)
    sources = {m.source.casefold() for m in mentions}
    diversity = min(100.0, len(sources) / 5 * 100)
    corroboration = min(100.0, len(mentions) / 5 * 100)
    components = ScoreComponents(
        negative_tone=round(tone, 1),
        reach=round(reach, 1),
        recency=round(recency, 1),
        source_diversity=round(diversity, 1),
        corroboration=round(corroboration, 1),
    )
    risk = 0.35 * tone + 0.20 * reach + 0.20 * recency + 0.15 * diversity + 0.10 * corroboration
    explanation = [
        f"{len(mentions)} mention(s) across {len(sources)} independent source(s)",
        f"combined estimated reach: {total_reach:,}",
        f"newest evidence is {newest_age:.0f} day(s) old",
        f"negative-tone component: {tone:.1f}/100",
    ]
    return round(risk, 1), components, explanation


def severity(risk: float) -> str:
    if risk >= 75:
        return "critical"
    if risk >= 50:
        return "high"
    if risk >= 25:
        return "moderate"
    return "low"
