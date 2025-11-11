from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from transformers import AutoTokenizer, EncoderDecoderModel


class ReviewModel:
    """Thin wrapper around the fine-tuned encoder-decoder model."""

    def __init__(self, model_dir: Path | str = Path("model/checkpoints/final"), base_model: str = "microsoft/codebert-base"):
        model_path = Path(model_dir)
        if model_path.exists():
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = EncoderDecoderModel.from_pretrained(model_path)
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(base_model)
            self.model = EncoderDecoderModel.from_encoder_decoder_pretrained(base_model, base_model)
        self.model.eval()

    def _format_input(self, payload: Dict) -> str:
        ctx = payload.get("context") or {}
        lint = payload.get("lint") or []
        lint_str = " | ".join(f"{item['code']}:{item['message']}" for item in lint) or "none"
        ctx_bits = [ctx.get("symbol_type"), ctx.get("symbol"), ctx.get("signature")]
        ctx_str = " | ".join([bit for bit in ctx_bits if bit]) or "N/A"
        return (
            f"File: {payload.get('path')}\n"
            f"Line: {payload.get('line')}\n"
            f"Diff:\n{payload.get('diff_hunk')}\n"
            f"Context: {ctx_str}\n"
            f"Lint: {lint_str}\n"
            "Provide a concise, constructive code review comment."
        )

    def generate_comment(self, payload: Dict, *, max_length: int = 128) -> str:
        prompt = self._format_input(payload)
        encoded = self.tokenizer(prompt, return_tensors="pt", truncation=True)
        output_ids = self.model.generate(
            **encoded,
            max_length=max_length,
            num_beams=4,
            early_stopping=True,
        )
        return self.tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()


_MODEL: Optional[ReviewModel] = None


def get_model(model_dir: Path | str | None = None) -> ReviewModel:
    global _MODEL
    if _MODEL is None:
        _MODEL = ReviewModel(model_dir=model_dir or Path("model/checkpoints/final"))
    return _MODEL
