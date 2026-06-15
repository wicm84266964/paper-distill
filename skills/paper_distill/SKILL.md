---
name: paper-distill
description: Build Chinese-first QA and multi-turn conversation datasets from markdown paper corpora by running one resumable paper-distill job per paper and exporting all paper artifacts into combined JSON/JSONL datasets.
---

# Paper Distill Skill

## Purpose

Use this skill when a coding agent needs to build a training dataset from a
markdown paper corpus by distilling each paper into structured question-answer
records, reusable paper knowledge maps, and multi-turn conversation records
without reimplementing the `paper_distill` subsystem.

This bundle is intentionally host-agnostic. It teaches a host how to invoke the already-existing command surface instead of embedding host-specific tool schemas.

All distillation outputs should be written in Chinese, even when the source paper is in English, because the downstream training target is a Chinese-base model.

`paper-distill run` is a single-paper operation by design, but the intended
workflow is corpus-scale. For hundreds or thousands of papers, invoke `run` once
per paper, with all papers sharing the same `--artifacts-root`. Each paper gets
its own artifact directory with a checkpoint, knowledge map, conversation plan,
conversation ledger, and QA ledger. `paper-distill export --artifacts-root ...`
then merges all valid paper artifact directories under that root into one
output dataset file.

## When to use

- The user wants to build a dataset from many markdown papers.
- The user wants to distill one markdown paper as one unit of a larger corpus workflow.
- The user wants each paper to produce multi-turn conversation records and QA pairs.
- The user wants to build a multi-paper training dataset by running one
  resumable distillation job per paper and exporting the shared artifacts root.
- The user wants to resume or restart a paper-specific distillation run.
- The user wants to export merged paper-distill outputs to `json` or `jsonl`.
- The user wants English-language papers to be distilled into Chinese training data.

## When not to use

- The request is about the main task runtime or web console.
- The input is not a markdown paper file.
- The user wants this package itself to manage a multi-paper queue, scheduling,
  or worker pool. Use an external script or scheduler for that.

## Stable entrypoints

Locate the bundle root before running commands. In an editable install or
source checkout, the bundle root is the directory that contains `pyproject.toml`
and the `app/` package.

```text
<paper-distill bundle root>
```

Prefer the installed script when available:

```powershell
paper-distill --help
```

Fallback to the module entrypoint when the installed script is unavailable:

```powershell
$root = "<paper-distill bundle root>"
$oldPythonPath = $env:PYTHONPATH
$env:PYTHONPATH = if ($oldPythonPath) { "$root;$oldPythonPath" } else { $root }
Push-Location $root
try {
  python -m app.paper_distill --help
} finally {
  Pop-Location
  $env:PYTHONPATH = $oldPythonPath
}
```

The agent may start from an arbitrary project cwd. When using the fallback
module entrypoint, always use the wrapper above so local package imports
resolve. Keep user paper paths, workspace roots, artifact roots, and output
paths explicit.

## Inputs

Required for `run`:

- `--paper <path>`
- exactly one of `--target-count <int>` or `--auto-target-count`

Optional for `run`:

- `--min-target-count <int>`
- `--max-target-count <int>`
- `--batch-size <int>`
- `--workspace-root <path>`
- `--artifacts-root <path>`
- `--cache-root <path>`
- `--backend mock|openai-compatible`
- `--model <name>`
- `--base-url <url>`
- `--api-key <secret>`
- `--timeout-seconds <float>`
- `--temperature <float>`
- `--restart`

Required for `export`:

- exactly one of `--artifact-dir <path>` or `--artifacts-root <path>`
- `--format json|jsonl|conversation-jsonl`
- `--output <path>`

## Default locations

- artifacts root: `data/paper_distill/papers`
- cache root: `data/paper_distill/cache`

When `--workspace-root` is omitted, these relative defaults resolve under `AGENT_WORKSPACE_ROOT` if it is set; otherwise they resolve under the current working directory.

Per-paper artifacts are written under:

```text
data/paper_distill/papers/<paper_id>/
  qa_entries.jsonl
  conversation_entries.jsonl
  checkpoint.json
  knowledge_map.json
  conversation_plan.json
```

`<paper_id>` is derived from the paper title plus a source hash. Re-running the
same paper resumes the same artifact directory unless `--restart` is used.

## Canonical commands

Run or resume distillation for one markdown paper:

```powershell
paper-distill run --paper papers/example.md --target-count 30 --batch-size 3 --backend mock
```

Run with automatic target sizing based on paper length, structure, and extracted paper signals:

```powershell
paper-distill run --paper papers/example.md --auto-target-count --min-target-count 8 --max-target-count 24 --batch-size 2 --backend mock
```

Export merged QA records from one artifacts root:

```powershell
paper-distill export --artifacts-root data/paper_distill/papers --format jsonl --output data/paper_distill/export.jsonl
```

Export one paper as one or more conversation records:

```powershell
paper-distill export --artifact-dir data/paper_distill/papers/<paper_id> --format conversation-jsonl --output data/paper_distill/conversation.jsonl
```

Build a corpus dataset by running each paper separately and exporting the shared
artifacts root:

```powershell
paper-distill run --paper papers/a.md --target-count 20 --backend openai-compatible --artifacts-root data/paper_distill/papers
paper-distill run --paper papers/b.md --target-count 20 --backend openai-compatible --artifacts-root data/paper_distill/papers
paper-distill export --artifacts-root data/paper_distill/papers --format jsonl --output data/paper_distill/all-papers.jsonl
paper-distill export --artifacts-root data/paper_distill/papers --format conversation-jsonl --output data/paper_distill/all-conversations.jsonl
```

External orchestration may run multiple papers in parallel, but never run two
workers against the same source paper and same artifacts root at the same time.

`--target-count` is the target number of accepted conversation turns for one
paper, not the number of papers. `--batch-size` controls how many candidate
turns the backend requests per generation call.

If `paper-distill` is not installed, run the same subcommands through:

```powershell
python -m app.paper_distill <subcommand> <args>
```

using the `Bundle root` wrapper from the stable entrypoints section.

## Success signals

`run` prints line-oriented status values such as:

- `paper_id=...`
- `artifact_dir=...`
- `target_count=...`
- `accepted_count=...`
- `entries_written=...`
- `cache_status=...`
- `status=completed|in_progress`

`export` prints:

- `output=...`
- `format=json|jsonl|conversation-jsonl`
- `record_count=...`

Treat the on-disk artifacts as the source of truth:

- `qa_entries.jsonl`
- `conversation_entries.jsonl`
- `checkpoint.json`
- `knowledge_map.json`
- `conversation_plan.json`
- exported `json` / `jsonl`

## Environment variables

Optional environment variables already supported by the CLI:

- `PAPER_DISTILL_BACKEND`
- `PAPER_DISTILL_MODEL`
- `PAPER_DISTILL_BASE_URL`
- `PAPER_DISTILL_API_KEY`

## Host adaptation notes

- Wrap the existing `paper-distill` CLI or `python -m app.paper_distill` entrypoint.
- Do not reimplement `app.paper_distill` internals in the host adapter.
- Keep host-specific tool schemas, slash commands, or permission models outside this bundle.
- If the host needs machine-native status parsing, read the generated artifact files in addition to stdout.
- When configuring prompts or adapters around this bundle, keep the generated knowledge maps, plans, questions, answers, and conversation records in Chinese.

## Non-goals

- This skill does not register a new host-specific runtime tool.
- This skill does not integrate with the main task runtime or web console.
- This skill does not alter prompt versions, artifact schema, or backend behavior.

## Reference

Operational details remain in the package README and CLI help.
