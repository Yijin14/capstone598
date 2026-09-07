# Research Experiment Memory Agent Baseline

This proposal baseline is a small, runnable rule-based system. It reads lab notes,
extracts experiment records, answers one historical experiment question, and writes
Markdown and JSON outputs.

## Run

From the repository root:

```bash
python3 proposal/run_baseline.py --input proposal/examples/lab_notes.txt --question proposal/examples/test_question.txt
```

## Inputs

- `proposal/examples/lab_notes.txt`: sample meeting notes and experiment records
- `proposal/examples/test_question.txt`: sample user question

## Outputs

- `proposal/outputs/baseline_output.md`
- `proposal/outputs/experiment_records.json`

## Limitations

- This baseline uses simple pattern matching, not an LLM or RAG.
- It only supports small text files.
- It does not provide line-level citations.
- It may miss fields when notes are written in a different style.
