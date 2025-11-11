from __future__ import annotations

import argparse
from pathlib import Path

from datasets import load_dataset
from transformers import AutoTokenizer


def format_prompt(example: dict) -> str:
    context = example.get("context") or {}
    ctx_bits = [
        context.get("symbol_type"),
        context.get("symbol"),
        context.get("signature"),
    ]
    ctx_str = " | ".join([bit for bit in ctx_bits if bit])
    lint = example.get("lint") or []
    lint_str = " | ".join(f"{item['code']}:{item['message']}" for item in lint)
    return (
        f"Review the following change:\n"
        f"File: {example['path']} (line {example['line']})\n"
        f"Diff:\n{example['diff_hunk']}\n"
        f"Context: {ctx_str or 'N/A'}\n"
        f"Lint: {lint_str or 'none'}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert examples JSONL to Hugging Face dataset.")
    parser.add_argument("--examples", type=Path, required=True)
    parser.add_argument("--model-name", default="microsoft/codebert-base")
    parser.add_argument("--out-dir", type=Path, default=Path("data/hf/code_review_ds"))
    args = parser.parse_args()

    dataset = load_dataset("json", data_files=str(args.examples))["train"]
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    def tokenize(batch):
        prompts = [format_prompt(ex) for ex in batch]
        comments = [ex["comment"] for ex in batch]

        model_inputs = tokenizer(prompts, truncation=True, padding="max_length", max_length=512)
        with tokenizer.as_target_tokenizer():
            labels = tokenizer(comments, truncation=True, padding="max_length", max_length=256)
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    tokenized = dataset.map(tokenize, batched=True, remove_columns=dataset.column_names)
    tokenized.save_to_disk(args.out_dir)
    print(f"Saved dataset to {args.out_dir}")


if __name__ == "__main__":
    main()
