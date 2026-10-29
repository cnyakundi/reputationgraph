from fastapi import FastAPI

from reputationgraph import __version__
from reputationgraph.models import AnalysisRequest, AnalysisResult
from reputationgraph.pipeline import analyze

app = FastAPI(
    title="ReputationGraph API",
    version=__version__,
    description="Explainable, source-backed reputation intelligence.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.post("/v1/analyze", response_model=AnalysisResult)
def analyze_mentions(request: AnalysisRequest) -> AnalysisResult:
    return analyze(request)
