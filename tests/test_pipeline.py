from datetime import UTC, datetime

from reputationgraph.models import AnalysisRequest, Mention
from reputationgraph.pipeline import analyze


def mention(id_: str, source: str, tags: list[str]) -> Mention:
    return Mention(
        id=id_,
        title="Acme faces safety complaint",
        text="A regulator opened an investigation into an unsafe product failure.",
        source=source,
        url=f"https://example.com/{id_}",
        published_at="2026-10-28T10:00:00Z",
        reach=10_000,
        tags=tags,
    )


def test_analysis_is_explainable_and_builds_graph() -> None:
    request = AnalysisRequest(
        subject="Acme",
        mentions=[mention("one", "Daily One", ["safety"]), mention("two", "Daily Two", ["safety"])],
        as_of=datetime(2026, 10, 29, tzinfo=UTC),
    )
    result = analyze(request)

    assert result.mention_count == 2
    assert result.overall_risk > 50
    assert result.narratives[0].name == "safety"
    assert result.narratives[0].components.negative_tone == 100
    assert str(result.narratives[0].evidence[0].url).startswith("https://example.com/")
    assert "2 mention(s) across 2 independent source(s)" in result.narratives[0].explanation
    assert any(node.kind == "subject" for node in result.nodes)
    assert any(edge.relation == "concerns" for edge in result.edges)


def test_tagged_mention_can_support_multiple_narratives() -> None:
    result = analyze(
        AnalysisRequest(
            subject="Acme",
            mentions=[mention("one", "Daily One", ["Safety", "Regulatory"])],
            as_of=datetime(2026, 10, 29, tzinfo=UTC),
        )
    )
    assert {item.name for item in result.narratives} == {"safety", "regulatory"}
