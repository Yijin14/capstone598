#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Experiment:
    experiment_id: str
    model: str
    dataset: str
    result: str
    issue: str
    decision: str
    source: str
    evidence: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def split_experiment_blocks(text: str) -> list[str]:
    matches = list(re.finditer(r"\bExperiment\s+E-\d{3}\b", text, re.IGNORECASE))
    if not matches:
        return [text]

    blocks: list[str] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append(text[start:end].strip())
    return blocks


def extract_first(pattern: str, text: str, default: str = "Unknown") -> str:
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if not match:
        return default
    return " ".join(match.group(1).strip().split())


def extract_experiment(block: str, source: Path) -> Experiment:
    experiment_id = extract_first(r"\b(Experiment\s+E-\d{3})\b", block)
    model = extract_first(r"\b(?:fine-tuned|used|trained)\s+([A-Za-z0-9_.-]+)", block)
    dataset = extract_first(r"\bon\s+the\s+([A-Za-z0-9_ .-]*Dataset)\b", block)
    result = extract_first(r"\b(?:reached|achieved|reported)\s+([0-9.]+%\s+[A-Za-z]+)", block)
    issue = extract_first(r"\b(?:However|but|Later)\s*,?\s*(.*?)(?:\.|$)", block)
    decision = extract_first(r"\bteam decided to\s+(.*?)(?:\.|$)", block)

    return Experiment(
        experiment_id=experiment_id,
        model=model,
        dataset=dataset,
        result=result,
        issue=issue,
        decision=decision,
        source=str(source),
        evidence=block,
    )


def tokenize(text: str) -> set[str]:
    stopwords = {
        "a",
        "an",
        "and",
        "before",
        "did",
        "do",
        "has",
        "have",
        "if",
        "is",
        "it",
        "on",
        "the",
        "this",
        "to",
        "we",
        "what",
    }
    return {
        word.lower()
        for word in re.findall(r"[A-Za-z0-9_-]+", text)
        if word.lower() not in stopwords and len(word) > 1
    }


def score(question: str, experiment: Experiment) -> int:
    question_terms = tokenize(question)
    record_terms = tokenize(
        " ".join(
            [
                experiment.experiment_id,
                experiment.model,
                experiment.dataset,
                experiment.result,
                experiment.issue,
                experiment.decision,
                experiment.evidence,
            ]
        )
    )
    return len(question_terms & record_terms)


def choose_best(question: str, experiments: list[Experiment]) -> Experiment | None:
    if not experiments:
        return None
    scored = sorted(((score(question, exp), exp) for exp in experiments), key=lambda x: x[0], reverse=True)
    return scored[0][1] if scored[0][0] > 0 else None


def build_answer(question: str, experiment: Experiment | None) -> str:
    if experiment is None:
        return f"""## Question

{question}

## Answer

I could not find a matching experiment in the provided notes.\n
"""

    return f"""## Question

{question}

## Answer

Yes. The notes contain a matching experiment: {experiment.experiment_id}.

## Experiment Details

- Model: {experiment.model}
- Dataset: {experiment.dataset}
- Result: {experiment.result}
- Reported issue: {experiment.issue}
- Decision: {experiment.decision}
- Source: {experiment.source}

## Reproduction Checklist

- Use the recorded model: {experiment.model}
- Use the recorded dataset: {experiment.dataset}
- Compare against the recorded result: {experiment.result}
- Account for the reported issue: {experiment.issue}
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Research Experiment Memory Agent baseline")
    parser.add_argument("--input", required=True, help="Path to lab notes text file")
    parser.add_argument("--question", required=True, help="Path to question text file")
    parser.add_argument("--output-dir", default="proposal/outputs", help="Directory for baseline outputs")
    args = parser.parse_args()

    input_path = Path(args.input)
    question_path = Path(args.question)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    notes = read_text(input_path)
    question = read_text(question_path).strip()

    experiments = [extract_experiment(block, input_path) for block in split_experiment_blocks(notes)]
    best = choose_best(question, experiments)
    answer = build_answer(question, best)

    (output_dir / "baseline_output.md").write_text(answer, encoding="utf-8")
    (output_dir / "experiment_records.json").write_text(
        json.dumps([asdict(exp) for exp in experiments], indent=2),
        encoding="utf-8",
    )

    print(answer)
    print(f"\nWrote {output_dir / 'baseline_output.md'}")
    print(f"Wrote {output_dir / 'experiment_records.json'}")


if __name__ == "__main__":
    main()
