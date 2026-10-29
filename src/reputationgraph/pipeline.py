from __future__ import annotations

import re
from collections import defaultdict
from datetime import UTC, datetime

from reputationgraph.models import (
    AnalysisRequest,
    AnalysisResult,
    Evidence,
    GraphEdge,
    GraphNode,
    Narrative,
)
from reputationgraph.scoring import score, severity

DEFAULT_NARRATIVE = "general coverage"


def _narrative_keys(title: str, tags: list[str]) -> list[str]:
    if tags:
        return sorted({tag.strip().casefold() for tag in tags if tag.strip()})
    words = re.findall(r"[a-z][a-z-]{3,}", title.casefold())
    stop = {"about", "after", "from", "into", "northstar", "report", "says", "with"}
    return [next((word for word in words if word not in stop), DEFAULT_NARRATIVE)]


def _entities(text: str, subject: str) -> set[str]:
    candidates = set(re.findall(r"\b[A-Z][\w&.-]*(?:\s+[A-Z][\w&.-]*){0,3}\b", text))
    return {item for item in candidates if item != subject and len(item) > 2}


def analyze(request: AnalysisRequest) -> AnalysisResult:
    as_of = request.as_of or datetime.now(UTC)
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=UTC)
    else:
        as_of = as_of.astimezone(UTC)

    clusters: dict[str, list] = defaultdict(list)
    for mention in request.mentions:
        for key in _narrative_keys(mention.title, mention.tags):
            clusters[key].append(mention)

    narratives: list[Narrative] = []
    nodes: dict[str, GraphNode] = {
        "subject": GraphNode(id="subject", label=request.subject, kind="subject")
    }
    edges: dict[tuple[str, str, str], GraphEdge] = {}

    def add_edge(source: str, target: str, relation: str) -> None:
        key = (source, target, relation)
        if key in edges:
            edges[key].weight += 1
        else:
            edges[key] = GraphEdge(source=source, target=target, relation=relation, weight=1)

    for index, (name, mentions) in enumerate(sorted(clusters.items())):
        risk, components, explanation = score(mentions, as_of)
        narratives.append(
            Narrative(
                name=name,
                mention_ids=sorted({m.id for m in mentions}),
                sources=sorted({m.source for m in mentions}),
                risk_score=risk,
                severity=severity(risk),
                components=components,
                explanation=explanation,
                evidence=[
                    Evidence(
                        mention_id=mention.id,
                        title=mention.title,
                        source=mention.source,
                        url=mention.url,
                        published_at=mention.published_at,
                    )
                    for mention in sorted(mentions, key=lambda item: item.published_at, reverse=True)
                ],
            )
        )
        narrative_id = f"narrative:{index}"
        nodes[narrative_id] = GraphNode(id=narrative_id, label=name, kind="narrative")
        add_edge(narrative_id, "subject", "concerns")
        for mention in mentions:
            source_id = f"source:{mention.source.casefold()}"
            nodes[source_id] = GraphNode(id=source_id, label=mention.source, kind="source")
            add_edge(source_id, narrative_id, "publishes")
            for entity in _entities(f"{mention.title} {mention.text}", request.subject):
                entity_id = f"entity:{entity.casefold()}"
                nodes[entity_id] = GraphNode(id=entity_id, label=entity, kind="entity")
                add_edge(entity_id, narrative_id, "co-occurs")

    narratives.sort(key=lambda item: item.risk_score, reverse=True)
    overall = round(max((item.risk_score for item in narratives), default=0.0), 1)
    return AnalysisResult(
        subject=request.subject,
        generated_at=as_of,
        mention_count=len(request.mentions),
        overall_risk=overall,
        narratives=narratives,
        nodes=sorted(nodes.values(), key=lambda node: node.id),
        edges=sorted(edges.values(), key=lambda edge: (edge.source, edge.target, edge.relation)),
    )
