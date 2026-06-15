# Paper Distill

中文说明见 [README.zh-CN.md](README.zh-CN.md).

Corpus-oriented Python package for distilling many Markdown papers into
Chinese-first QA and multi-turn conversation training datasets.

The execution unit is one paper at a time, but the intended workflow is a
large literature corpus: run each paper into its own resumable artifact
directory, then export all paper artifacts into one combined dataset file.

## What It Does

- Builds large paper-derived datasets from hundreds or thousands of Markdown
  papers by running one resumable paper job per invocation.
- Stores each paper in its own artifact directory under the shared
  `artifacts_root`.
- Builds a reusable paper knowledge map and a per-paper conversation plan.
- Generates multi-turn conversation turns for each paper; each paper can export
  one or more conversation records, grouped by planned thread.
- Exports either one paper or every valid paper under an `artifacts_root` into
  one combined dataset file.
- Exports QA records and conversation records as `json`, `jsonl`, or
  `conversation-jsonl`.
- Writes generated questions, answers, knowledge maps, and conversations in
  Chinese even when the source paper is English.
- Supports resumable runs and deterministic smoke tests through a built-in
  `mock` backend.

## Requirements

- Python 3.12+
- Runtime dependency: `httpx`
- Optional for real generation: an OpenAI-compatible chat completions endpoint
  and API key

No desktop software, database server, GPU runtime, or local model service is
required. The `mock` backend runs without network model access.

## Install

```powershell
python -m pip install -e .
```

For tests:

```powershell
python -m pip install -e ".[dev]"
python -m pytest tests -q
```

## Single-paper Smoke Test

Create a tiny Markdown paper:

```powershell
New-Item -ItemType Directory -Force papers | Out-Null
@"
# Example Paper

The study introduces a simple method for extracting reusable findings from
scientific text. The method records evidence and exports training examples.
"@ | Set-Content -Encoding UTF8 papers\example.md
```

Run one paper job with the mock backend:

```powershell
paper-distill run --paper papers\example.md --target-count 3 --batch-size 2 --backend mock
```

Export conversation records from the shared artifacts root:

```powershell
paper-distill export --artifacts-root data\paper_distill\papers --format conversation-jsonl --output data\paper_distill\conversation.jsonl
```

## Corpus Workflow

`paper-distill run` is intentionally single-paper because each paper needs its
own checkpoint, knowledge map, conversation plan, conversation ledger, and QA
ledger. This makes large runs easier to resume and audit.

For a literature corpus, call `run` once per paper, using the same
`--artifacts-root`:

```powershell
paper-distill run --paper papers\a.md --target-count 20 --backend openai-compatible --artifacts-root data\paper_distill\papers
paper-distill run --paper papers\b.md --target-count 20 --backend openai-compatible --artifacts-root data\paper_distill\papers
paper-distill run --paper papers\c.md --target-count 20 --backend openai-compatible --artifacts-root data\paper_distill\papers
```

Each paper gets a separate directory:

```text
data/paper_distill/papers/
  paper-a--<hash>/
  paper-b--<hash>/
  paper-c--<hash>/
```

Inside each paper directory, the tool writes the paper-specific artifacts:

```text
qa_entries.jsonl
conversation_entries.jsonl
checkpoint.json
knowledge_map.json
conversation_plan.json
```

`conversation_entries.jsonl` stores generated conversation turns. During
`conversation-jsonl` export, turns are grouped by planned thread into multi-turn
conversation records with `messages` and `turns` arrays.

Then export the whole corpus into one dataset file:

```powershell
paper-distill export --artifacts-root data\paper_distill\papers --format jsonl --output data\paper_distill\all-papers.jsonl
paper-distill export --artifacts-root data\paper_distill\papers --format conversation-jsonl --output data\paper_distill\all-conversations.jsonl
```

To export only one paper, use `--artifact-dir`:

```powershell
paper-distill export --artifact-dir data\paper_distill\papers\<paper_id> --format conversation-jsonl --output data\paper_distill\one-paper.jsonl
```

External scripts may run multiple `paper-distill run` commands in parallel, but
each paper should write to its own paper artifact directory. Avoid launching two
workers for the same source paper and same `artifacts_root` at the same time.

`--target-count` is the target number of accepted conversation turns for one
paper. It is not the number of papers to process. `--batch-size` controls how
many candidate turns the backend asks for in one generation call.

## Real Model Backend

Use any OpenAI-compatible chat completions service:

```powershell
$env:PAPER_DISTILL_BACKEND = "openai-compatible"
$env:PAPER_DISTILL_MODEL = "<model name>"
$env:PAPER_DISTILL_BASE_URL = "<https://provider.example/v1>"
$env:PAPER_DISTILL_API_KEY = "<api key>"

paper-distill run --paper papers\example.md --auto-target-count --backend openai-compatible
```

The package rejects non-localhost plain HTTP endpoints and base URLs with
embedded credentials.

## Outputs

Default artifacts are written under:

```text
data/paper_distill/papers/<paper_id>/
  qa_entries.jsonl
  conversation_entries.jsonl
  checkpoint.json
  knowledge_map.json
  conversation_plan.json
```

`<paper_id>` is derived from the paper title plus a source hash, so repeated runs
of the same paper resume the same artifact directory unless `--restart` is used.

Use `--workspace-root`, `--artifacts-root`, and `--cache-root` to place outputs
somewhere else.

## Agent Contract

An optional agent-facing contract is included at:

```text
skills/paper_distill/SKILL.md
```

That file explains when an automation agent should use this package and how to
call the CLI without reimplementing the distillation logic. It is optional; the
Python CLI is the stable public interface.

## License

MIT.
