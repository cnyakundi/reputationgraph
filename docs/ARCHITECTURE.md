# Architecture

ReputationGraph uses a small ports-and-adapters design. The public schema is the
contract: every downstream score must remain traceable to a URL, source, and
timestamp.

## Pipeline

1. **Normalization** validates bounded input, timezone-aware dates, and URLs.
2. **Narrative detection** groups explicit tags or deterministic title features.
3. **Entity extraction** identifies likely proper nouns for graph exploration.
4. **Scoring** combines five visible components with versioned weights.
5. **Projection** emits API JSON or a standalone HTML intelligence brief.

The deterministic demo implementation is intentionally replaceable. A production
adapter might use a queue-backed feed collector, a transformer for entity
resolution, PostgreSQL with pgvector for clustering, and a graph database for
cross-matter research. Those adapters should preserve the `Mention` and
`AnalysisResult` evidence contracts.

## Trust boundaries

- URLs and mention text are untrusted input and are never fetched by the core.
- HTML output escapes all user-controlled fields.
- API payloads have length and count limits.
- Scores describe monitoring priority, not truth, guilt, or legal conclusions.
- Collection adapters must respect source terms, privacy law, and robots policy.

## Non-goals

The project does not automate reviews, personas, takedowns, engagement, mass
messaging, or content suppression. Response actions require human judgment.
