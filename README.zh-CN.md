# Paper Distill

用于把大量 Markdown 论文蒸馏成 QA / 多轮对话训练数据集的独立 Python 包。

它的执行粒度是“每次处理一篇论文”，但目标工作流是文献库级别的：对上百篇或
上千篇论文逐篇运行、逐篇保存可续跑 artifact，最后把所有论文 artifact 合并导出
成一个大训练数据集。

## 它能做什么

- 面向大规模文献集合构建训练数据：每次 `paper-distill run` 跑一篇论文，外部
  脚本或调度器负责遍历整个论文库。
- 每篇论文会写入共享 `artifacts_root` 下自己的独立 artifact 目录。
- 为每篇论文生成可复用的知识图谱和对话规划。
- 为每篇论文生成多轮连续对话 turn；导出时一篇论文可以形成一个或多个按 thread
  聚合的多轮 conversation 记录。
- 导出时既可以只导出一篇论文，也可以把同一个 `artifacts_root` 下的所有论文合并成一个大数据集文件。
- 导出 `json`、`jsonl`、`conversation-jsonl` 格式的 QA / 对话训练记录。
- 支持配置生成问题、回答、知识图谱和对话记录时使用的目标语言。
- 支持断点续跑。
- 内置 `mock` backend，可以不接模型服务就做 smoke test。

## 环境要求

- Python 3.12+
- 运行依赖：`httpx`
- 可选：OpenAI-compatible chat completions 接口和 API key，用于真实模型生成

不需要桌面软件、数据库服务、GPU、Blender 或本地大模型服务。使用 `mock`
backend 时不需要联网模型接口。

## 安装

```powershell
python -m pip install -e .
```

如果要跑测试：

```powershell
python -m pip install -e ".[dev]"
python -m pytest tests -q
```

## 单篇论文快速验证

创建一个很小的 Markdown 论文：

```powershell
New-Item -ItemType Directory -Force papers | Out-Null
@"
# Example Paper

The study introduces a simple method for extracting reusable findings from
scientific text. The method records evidence and exports training examples.
"@ | Set-Content -Encoding UTF8 papers\example.md
```

用 `mock` backend 跑一个单篇论文任务：

```powershell
paper-distill run --paper papers\example.md --target-count 3 --batch-size 2 --backend mock
```

从共享 artifacts root 导出对话训练记录：

```powershell
paper-distill export --artifacts-root data\paper_distill\papers --format conversation-jsonl --output data\paper_distill\conversation.jsonl
```

## 多论文工作流

`paper-distill run` 是单篇论文入口，因为每篇论文都需要自己的 checkpoint、
知识图谱、对话规划、conversation ledger 和 QA ledger。这样更适合上千篇文献
的断点续跑、失败重试和结果审计。

处理论文集合时，对每篇论文分别调用一次 `run`，并使用同一个
`--artifacts-root`：

```powershell
paper-distill run --paper papers\a.md --target-count 20 --backend openai-compatible --artifacts-root data\paper_distill\papers
paper-distill run --paper papers\b.md --target-count 20 --backend openai-compatible --artifacts-root data\paper_distill\papers
paper-distill run --paper papers\c.md --target-count 20 --backend openai-compatible --artifacts-root data\paper_distill\papers
```

每篇论文会得到独立目录：

```text
data/paper_distill/papers/
  paper-a--<hash>/
  paper-b--<hash>/
  paper-c--<hash>/
```

每个论文目录内部会写入：

```text
qa_entries.jsonl
conversation_entries.jsonl
checkpoint.json
knowledge_map.json
conversation_plan.json
```

`conversation_entries.jsonl` 保存这篇论文生成的对话 turn。导出
`conversation-jsonl` 时，这些 turn 会按规划好的 thread 聚合成多轮 conversation
记录，记录里包含 `messages` 和 `turns`。

之后可以把整个论文集合导出成一个训练数据集：

```powershell
paper-distill export --artifacts-root data\paper_distill\papers --format jsonl --output data\paper_distill\all-papers.jsonl
paper-distill export --artifacts-root data\paper_distill\papers --format conversation-jsonl --output data\paper_distill\all-conversations.jsonl
```

如果只想导出某一篇论文，用 `--artifact-dir`：

```powershell
paper-distill export --artifact-dir data\paper_distill\papers\<paper_id> --format conversation-jsonl --output data\paper_distill\one-paper.jsonl
```

外部脚本可以并发启动多个 `paper-distill run`，但每个 worker 应处理不同论文。
不要同时让两个 worker 对同一篇论文和同一个 `artifacts_root` 写入。

`--target-count` 表示单篇论文要生成/接受的 conversation turn 数量，不是论文
数量。`--batch-size` 表示每次模型调用请求多少个候选 turn。

## 目标语言

为了兼容原始工作流，生成字段默认使用 Chinese，但目标语言可以配置：

```powershell
paper-distill run --paper papers\example.md --target-count 20 --target-language English --backend openai-compatible
```

也可以通过环境变量设置：

```powershell
$env:PAPER_DISTILL_TARGET_LANGUAGE = "English"
```

如果希望生成字段跟随每篇论文的原文主语言，可以使用 `source language`。

## 使用真实模型

真实生成时，使用任意 OpenAI-compatible chat completions 服务：

```powershell
$env:PAPER_DISTILL_BACKEND = "openai-compatible"
$env:PAPER_DISTILL_MODEL = "<model name>"
$env:PAPER_DISTILL_BASE_URL = "<https://provider.example/v1>"
$env:PAPER_DISTILL_API_KEY = "<api key>"
$env:PAPER_DISTILL_TARGET_LANGUAGE = "English"

paper-distill run --paper papers\example.md --auto-target-count --backend openai-compatible
```

出于安全考虑，包会拒绝非 localhost 的明文 HTTP endpoint，也会拒绝在
`base_url` 中嵌入用户名或密码。

## 默认输出

默认产物会写到：

```text
data/paper_distill/papers/<paper_id>/
  qa_entries.jsonl
  conversation_entries.jsonl
  checkpoint.json
  knowledge_map.json
  conversation_plan.json
```

`<paper_id>` 由论文标题和 source hash 生成；同一篇论文重复运行时会续写/续跑
同一个 artifact 目录，除非显式使用 `--restart`。

可以用 `--workspace-root`、`--artifacts-root`、`--cache-root` 调整输出位置。

## 智能体合约

仓库内包含一个可选的智能体调用合约：

```text
skills/paper_distill/SKILL.md
```

这个文件说明自动化智能体什么时候应该使用本包，以及如何调用 CLI，而不是重新
实现论文蒸馏逻辑。它不是必需入口；稳定的公开接口是 Python CLI。

## 许可证

MIT。
