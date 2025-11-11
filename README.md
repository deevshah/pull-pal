# Pull Pal

Pull Pal is a context-aware code review assistant that ingests GitHub pull requests, enriches diffs with AST context and lint diagnostics, and trains a transformer model to produce natural review comments.

## Components

1. **PR Fetcher** – Downloads PR metadata and unified diffs from GitHub.
2. **Diff Parser** – Converts patch files into structured JSON summaries.
3. **AST Context Enricher** – Clones the repo and captures surrounding symbols for changed lines.
4. **Linter Integration** – Runs `flake8` on the touched files and maps warnings to diff lines.
5. **Comment Fetcher** – Retrieves existing threaded review comments for supervision.
6. **Example Builder** – Aligns diffs, context, lint, and review comments into training examples.
7. **HF Dataset Formatter** – Builds a Hugging Face dataset and tokenizes it with CodeBERT.
8. **Training** – Fine-tunes `microsoft/codebert-base` on the curated examples.
9. **Inference Service** – FastAPI endpoint that suggests review comments.
10. **GitHub Action** – Calls the inference endpoint and posts inline feedback.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export GITHUB_TOKEN=...  # required for GitHub API calls
python scripts/fetch_pr.py --owner octocat --repo hello-world --pr 123
python scripts/diff_parser.py data/raw/octocat_hello-world/pr_123/diff.patch
```

See individual script docstrings for more usage instructions.
