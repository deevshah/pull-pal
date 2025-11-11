from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from .inference import get_model


class ContextPayload(BaseModel):
    path: Optional[str] = None
    line: Optional[int] = None
    symbol: Optional[str] = None
    symbol_type: Optional[str] = None
    signature: Optional[str] = None


class LintPayload(BaseModel):
    code: str
    message: str
    line: Optional[int] = None


class ReviewRequest(BaseModel):
    path: str
    line: int
    diff_hunk: str
    context: Optional[ContextPayload] = None
    lint: Optional[List[LintPayload]] = None


class ReviewResponse(BaseModel):
    comment: str


app = FastAPI(title="Pull Pal API", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/review", response_model=ReviewResponse)
def review(payload: ReviewRequest) -> ReviewResponse:
    model = get_model(Path("model/checkpoints/final"))
    comment = model.generate_comment(payload.model_dump())
    return ReviewResponse(comment=comment)
