# Novel CLI 应用设计文档：全局安装版

## 1. 项目目标

本 CLI 应用用于封装 DeepSeek 调用能力，为多个小说项目提供统一的续写、润色、改写、摘要、上下文预览等命令行接口。

它不是某一个小说项目内部的源码，而是一个可以全局安装的通用 CLI 应用。安装后，任何小说项目只要遵循约定目录结构，或者提供项目配置文件，就可以直接使用同一个 `novel` 命令。

推荐最终使用方式：

```bash
novel polish chapters/003.md
novel continue chapters/003.md
novel summarize chapters/003.md
novel rewrite chapters/003.md --instruction "语言更冷峻，减少解释性心理描写"
```

核心分工：

```text
全局 novel CLI：稳定执行写作任务、调用 DeepSeek、保存输出
小说项目目录：保存章节、设定、提示词、摘要、草稿和项目配置
Codex：理解用户意图、选择文件、调用 novel 命令、检查结果
AGENTS.md / skill：告诉 Codex 本项目如何使用全局 novel CLI
```

## 2. 整体工作原理

CLI 的工作流程如下：

```text
用户或 Codex 在小说项目目录中发起命令
        ↓
全局 novel CLI 解析命令和参数
        ↓
CLI 定位当前小说项目根目录
        ↓
读取项目配置、章节文件、风格指南、人物设定、世界观、时间线、前情摘要
        ↓
根据任务类型选择提示词模板
        ↓
拼接最终 prompt
        ↓
调用 DeepSeek API
        ↓
将生成结果写入当前项目的 drafts/ 或 summaries/
        ↓
输出结构化执行结果，供用户或 Codex 阅读
```

CLI 需要完成的事情包括：

1. 在任意小说项目中运行，而不要求项目内包含 CLI 源码。
2. 自动识别项目根目录。
3. 根据命令类型选择任务模式，例如 polish、continue、rewrite、summarize。
4. 读取当前小说项目中的上下文文件。
5. 使用项目自定义提示词模板或 CLI 内置默认模板构造完整 prompt。
6. 调用 DeepSeek API 获取生成结果。
7. 将结果保存到当前项目的安全位置，默认不覆盖原文。
8. 输出执行状态、输入文件、输出文件、模型名称等信息。

## 3. 与 Codex 的关系

本 CLI 应用应被设计成 Codex 能够稳定调用的全局命令。

Codex 不应该每次临时拼接复杂的 Python 命令，也不应该直接处理 DeepSeek API 细节。更推荐的分工如下：

```text
Codex：理解用户意图、选择文件、调用命令、检查结果
全局 CLI：稳定执行写作任务、调用 DeepSeek、保存输出
小说项目：保存章节、设定、风格、人物、时间线、提示词
AGENTS.md / skill：告诉 Codex 本项目有哪些约定和命令规则
```

例如，用户在某个小说项目中对 Codex 说：

```text
请润色 chapters/003.md，保持剧情不变，语言更克制。
```

Codex 应调用：

```bash
novel polish chapters/003.md --instruction "保持剧情不变，语言更克制"
```

全局 CLI 会在当前项目中读取配置和上下文，并输出到：

```text
drafts/003.polished.md
```

Codex 再向用户汇报输出文件路径和注意事项。

## 4. 全局 CLI 与小说项目的推荐结构

全局 CLI 源码应放在独立仓库中，例如：

```text
novel-cli/
  pyproject.toml
  README.md

  novel_cli/
    __init__.py
    cli.py
    config.py
    deepseek_client.py
    project_detector.py
    context_loader.py
    prompt_builder.py
    file_utils.py
    output.py

  novel_cli/templates/
    prompts/
      polish.md
      continue.md
      rewrite.md
      summarize.md
      outline.md
    project/
      novel.yaml
      AGENTS.md
```

每个小说项目只需要保存项目数据和配置，例如：

```text
my-novel/
  AGENTS.md
  novel.yaml
  .env
  .gitignore

  prompts/
    polish.md
    continue.md
    rewrite.md
    summarize.md

  docs/
    style.md
    characters.md
    worldbuilding.md
    timeline.md
    glossary.md

  chapters/
    001.md
    002.md
    003.md

  drafts/
    003.polished.md
    003.continued.md

  summaries/
    001.md
    002.md
    story-so-far.md

  .agents/
    skills/
      novel-deepseek/
        SKILL.md
```

### 4.1 全局 CLI 源码目录 `novel_cli/`

这是 CLI 应用自身的源码目录，安装后不需要复制到小说项目中。

建议模块职责：

| 文件 | 职责 |
|---|---|
| `cli.py` | 解析命令行参数，分发任务 |
| `config.py` | 读取全局配置、项目配置和环境变量 |
| `deepseek_client.py` | 调用 DeepSeek API |
| `project_detector.py` | 识别当前小说项目根目录 |
| `context_loader.py` | 从当前项目读取章节、设定、摘要等上下文 |
| `prompt_builder.py` | 将模板和上下文拼接成最终 prompt |
| `file_utils.py` | 生成输出路径、避免覆盖原文 |
| `output.py` | 打印人类可读和机器可读结果 |

### 4.2 小说项目中的 `novel.yaml`

每个小说项目建议提供一个 `novel.yaml`，用于声明项目目录、默认模型和上下文文件。

示例：

```yaml
project_name: my-novel
language: zh-CN

model:
  provider: deepseek
  name: deepseek-chat
  temperature: 0.7

paths:
  chapters: chapters
  drafts: drafts
  summaries: summaries
  prompts: prompts
  docs: docs

context:
  style: docs/style.md
  characters: docs/characters.md
  worldbuilding: docs/worldbuilding.md
  timeline: docs/timeline.md
  glossary: docs/glossary.md
  story_so_far: summaries/story-so-far.md

output:
  overwrite: false
  version_existing_files: true
```

`novel.yaml` 的作用是让同一个全局 CLI 可以适配不同小说项目。

如果项目没有 `novel.yaml`，CLI 可以使用默认约定：

```text
chapters/
drafts/
summaries/
prompts/
docs/
```

### 4.3 小说项目中的 `prompts/`

保存项目自定义提示词模板。项目内模板优先级应高于 CLI 内置模板。

示例：

```text
prompts/polish.md
prompts/continue.md
prompts/rewrite.md
prompts/summarize.md
```

如果某个模板不存在，CLI 可以回退到内置默认模板。

### 4.4 小说项目中的 `docs/`

保存小说项目知识库。

常见文件：

| 文件 | 内容 |
|---|---|
| `style.md` | 文风、叙事节奏、禁忌表达 |
| `characters.md` | 人物设定、关系、说话方式 |
| `worldbuilding.md` | 世界观、规则、地点、阵营 |
| `timeline.md` | 时间线和事件顺序 |
| `glossary.md` | 专有名词和译名统一 |

### 4.5 小说项目中的 `chapters/`

正式章节目录。CLI 默认不应该覆盖这里的文件。

### 4.6 小说项目中的 `drafts/`

AI 生成正文输出目录。续写、润色、改写结果默认保存到这里。

### 4.7 小说项目中的 `summaries/`

章节摘要目录。摘要任务默认输出到这里。

## 5. 安装方式

推荐将 CLI 应用作为独立 Python package 安装。

### 5.1 CLI 应用仓库的 `pyproject.toml`

```toml
[project]
name = "novel-cli"
version = "0.1.0"
description = "Global CLI for novel writing with DeepSeek"
requires-python = ">=3.10"
dependencies = [
  "openai>=1.0.0",
  "python-dotenv>=1.0.0",
  "pyyaml>=6.0.0",
]

[project.scripts]
novel = "novel_cli.cli:main"
```

### 5.2 开发安装

在 `novel-cli/` 源码仓库中执行：

```bash
pip install -e .
```

安装后，在任意目录都可以运行：

```bash
novel --help
```

### 5.3 使用 pipx 安装

如果希望作为真正的全局命令使用，推荐使用 `pipx`：

```bash
pipx install /path/to/novel-cli
```

开发阶段可以使用：

```bash
pipx install -e /path/to/novel-cli
```

安装完成后，在任何小说项目目录下都可以直接调用：

```bash
novel polish chapters/003.md
```

### 5.4 初始化小说项目

建议全局 CLI 提供初始化命令：

```bash
novel init
```

它会在当前目录生成：

```text
novel.yaml
AGENTS.md
prompts/
docs/
chapters/
drafts/
summaries/
```

也可以提供：

```bash
novel init --minimal
```

只生成最少文件：

```text
novel.yaml
chapters/
drafts/
summaries/
```

## 6. 环境变量和配置

DeepSeek API Key 不应写入代码、prompt、skill、AGENTS.md 或 `novel.yaml`。

推荐支持三层配置：

```text
1. 命令行参数：优先级最高
2. 当前项目的 novel.yaml 和 .env
3. 用户级全局配置：~/.config/novel-cli/config.yaml 和环境变量
```

### 6.1 项目 `.env`

小说项目可以放 `.env`：

```env
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

`.gitignore` 中必须忽略 `.env`：

```gitignore
.env
```

### 6.2 用户级全局配置

为了避免每个项目都配置 API key，也可以支持用户级配置文件：

```text
~/.config/novel-cli/config.yaml
```

示例：

```yaml
deepseek:
  base_url: https://api.deepseek.com
  model: deepseek-chat
```

API key 仍建议使用环境变量或系统密钥管理，不建议明文写入配置文件。

### 6.3 缺少 API key 的错误

CLI 启动时应读取 `.env` 和系统环境变量。如果缺少 `DEEPSEEK_API_KEY`，应给出清晰错误：

```text
Missing DEEPSEEK_API_KEY. Please set it in your environment or project .env file.
```

## 7. 命令设计

### 7.1 基础命令

```bash
novel init
novel polish <chapter-file>
novel continue <chapter-file>
novel rewrite <chapter-file>
novel summarize <chapter-file>
```

### 7.2 推荐扩展命令

```bash
novel context <chapter-file>
novel check <chapter-file>
novel update-story-so-far
novel outline <topic-or-file>
novel config show
novel config doctor
```

### 7.3 通用参数

建议所有生成类命令支持以下参数：

```text
--project <path>           指定小说项目根目录，默认自动检测
--out <path>               指定输出路径
--instruction <text>       用户额外要求
--model <name>             指定 DeepSeek 模型
--temperature <float>      控制随机性
--prompt <path>            指定提示词模板
--dry-run                  只生成 prompt，不调用 API
--json                     以 JSON 格式输出执行结果
--overwrite                允许覆盖输出文件，默认不允许
```

### 7.4 项目根目录检测

CLI 应按以下顺序确定项目根目录：

1. 如果传入 `--project`，使用该路径。
2. 从当前工作目录向上查找 `novel.yaml`。
3. 如果未找到 `novel.yaml`，但当前目录包含 `chapters/`，则使用当前目录。
4. 如果仍无法确定项目根目录，提示用户运行 `novel init` 或传入 `--project`。

### 7.5 默认行为

命令应该尽可能短，例如：

```bash
novel polish chapters/003.md
```

CLI 内部自动使用当前项目中的默认文件：

```text
prompts/polish.md
docs/style.md
docs/characters.md
docs/worldbuilding.md
docs/timeline.md
summaries/story-so-far.md
```

如果项目中缺少某个 prompt 模板，则回退到 CLI 内置模板。

如果某些上下文文件不存在，CLI 不应直接失败，而应继续执行并打印警告。

## 8. 各命令语义

## 8.1 `novel init`

用于初始化一个小说项目。

示例：

```bash
novel init
```

生成：

```text
novel.yaml
AGENTS.md
prompts/
docs/
chapters/
drafts/
summaries/
```

初始化时应避免覆盖已有文件。如果文件已存在，应跳过或提示使用 `--force`。

可选参数：

```text
--minimal       只生成最小目录和 novel.yaml
--force         允许覆盖初始化模板文件
--language zh-CN
```

## 8.2 `novel polish`

用于润色已有章节。

示例：

```bash
novel polish chapters/003.md
```

带额外要求：

```bash
novel polish chapters/003.md --instruction "语言更冷峻，减少网文感"
```

默认输出：

```text
drafts/003.polished.md
```

语义要求：

- 不改变主要剧情。
- 不改变人物动机。
- 不新增重大设定。
- 优化句子节奏、画面感、对话自然度。
- 删除重复、解释过度、口号化表达。
- 保留原文核心信息。

## 8.3 `novel continue`

用于从指定章节结尾继续写作。

示例：

```bash
novel continue chapters/003.md
```

带额外要求：

```bash
novel continue chapters/003.md --instruction "继续写冲突升级，不要跳到第二天"
```

默认输出：

```text
drafts/003.continued.md
```

语义要求：

- 从原文最后一段自然接续。
- 不要总结剧情，要输出小说正文。
- 优先延续当前冲突。
- 保持人物声音、世界观规则、时间线一致。
- 不要突然引入无铺垫的重大设定。

## 8.4 `novel rewrite`

用于按用户指令定向改写。

示例：

```bash
novel rewrite chapters/003.md --instruction "改成第一人称，增强主角的压迫感"
```

默认输出：

```text
drafts/003.rewritten.md
```

语义要求：

- 可以改变表达方式、视角、段落结构。
- 默认不改变核心剧情和设定。
- 必须遵守用户的 `--instruction`。
- 如果用户要求会破坏已有设定，应在结果说明中提醒。

## 8.5 `novel summarize`

用于生成章节摘要。

示例：

```bash
novel summarize chapters/003.md
```

默认输出：

```text
summaries/003.md
```

摘要建议包含：

```markdown
# Chapter 003 Summary

## 本章主要事件

## 人物状态变化

## 新增设定

## 伏笔和未解决问题

## 时间线变化

## 后续续写注意事项
```

## 8.6 `novel context`

用于预览将发送给 DeepSeek 的上下文。

示例：

```bash
novel context chapters/003.md --mode polish
```

此命令不调用 DeepSeek，只输出：

```text
Project root: /path/to/my-novel
Mode: polish
Prompt template: prompts/polish.md 或 <built-in polish template>
Chapter: chapters/003.md
Style: docs/style.md
Characters: docs/characters.md
Worldbuilding: docs/worldbuilding.md
Timeline: docs/timeline.md
Story so far: summaries/story-so-far.md
Estimated prompt length: ...
Output path: drafts/003.polished.md
```

这个命令非常适合 Codex 在执行生成前检查上下文是否正确。

## 8.7 `novel config doctor`

用于检查当前环境和项目配置是否可用。

示例：

```bash
novel config doctor
```

应检查：

```text
是否能定位项目根目录
是否存在 novel.yaml
是否存在 chapters/、drafts/、summaries/
是否存在 DEEPSEEK_API_KEY
是否能找到 prompt 模板
是否存在关键上下文文件
```

## 9. 输出路径规则

CLI 默认不覆盖原文。

输入：

```text
chapters/003.md
```

默认输出：

| 命令 | 默认输出 |
|---|---|
| `polish` | `drafts/003.polished.md` |
| `continue` | `drafts/003.continued.md` |
| `rewrite` | `drafts/003.rewritten.md` |
| `summarize` | `summaries/003.md` |

如果输出文件已存在，应自动生成新版本：

```text
drafts/003.polished.v2.md
drafts/003.polished.v3.md
```

只有在用户显式传入 `--overwrite` 时，才允许覆盖输出文件。

所有相对路径都应基于项目根目录解析，而不是基于 CLI 安装目录。

## 10. Prompt 构造原则

CLI 应优先使用项目中的模板文件，其次使用 CLI 内置默认模板。

模板查找顺序：

```text
1. --prompt 显式指定的模板
2. 当前项目 prompts/<mode>.md
3. CLI 内置模板 novel_cli/templates/prompts/<mode>.md
```

### 10.1 模板变量

建议支持这些变量：

```text
{{CHAPTER_TEXT}}
{{STYLE_GUIDE}}
{{CHARACTERS}}
{{WORLDBUILDING}}
{{TIMELINE}}
{{STORY_SO_FAR}}
{{GLOSSARY}}
{{INSTRUCTION}}
```

### 10.2 润色 prompt 示例

`prompts/polish.md`：

```markdown
# 润色任务

你正在润色一部长篇中文小说。

## 目标

- 保持原剧情不变
- 保持人物动机不变
- 保持世界观设定不变
- 优化语言节奏、画面感、心理描写和对话自然度
- 删除重复、解释过度、口号化表达
- 不要把文本改成总结或大纲

## 风格要求

{{STYLE_GUIDE}}

## 人物设定

{{CHARACTERS}}

## 世界观

{{WORLDBUILDING}}

## 原文

{{CHAPTER_TEXT}}

## 额外要求

{{INSTRUCTION}}

## 输出要求

只输出润色后的小说正文，不要解释修改过程。
```

### 10.3 续写 prompt 示例

`prompts/continue.md`：

```markdown
# 续写任务

你正在续写一部长篇中文小说。

## 续写原则

- 从原文最后一段自然接续
- 不要跳过关键场景
- 不要总结剧情，要写成正文
- 保持人物声音、世界观规则、时间线一致
- 不要突然引入重大设定，除非上下文已有伏笔
- 优先延续当前冲突，而不是开启完全无关的新事件

## 前情摘要

{{STORY_SO_FAR}}

## 人物设定

{{CHARACTERS}}

## 世界观

{{WORLDBUILDING}}

## 时间线

{{TIMELINE}}

## 风格指南

{{STYLE_GUIDE}}

## 当前章节

{{CHAPTER_TEXT}}

## 额外要求

{{INSTRUCTION}}

## 输出要求

只输出续写正文。
```

## 11. DeepSeek 调用设计

`deepseek_client.py` 应只负责 API 调用，不负责项目业务逻辑。

建议接口：

```python
def call_deepseek(
    prompt: str,
    model: str,
    temperature: float,
    system_prompt: str | None = None,
) -> str:
    ...
```

推荐行为：

1. 从环境变量读取 `DEEPSEEK_API_KEY`。
2. 从环境变量、用户级配置、项目配置或参数读取 `DEEPSEEK_BASE_URL`。
3. 使用 OpenAI 兼容 SDK 或 HTTP 请求调用 DeepSeek。
4. 对缺少 API key、网络错误、API 错误给出清晰异常。
5. 返回纯文本结果。

## 12. 错误处理

CLI 应避免静默失败。

常见错误和建议输出：

| 场景 | 行为 |
|---|---|
| 无法定位项目根目录 | 失败，提示运行 `novel init` 或使用 `--project` |
| 输入章节不存在 | 直接失败，提示路径不存在 |
| 缺少 API key | 直接失败，提示设置 `DEEPSEEK_API_KEY` |
| prompt 模板不存在 | 如无内置模板则失败，提示缺少哪个模板 |
| 可选上下文文件不存在 | 打印 warning，继续执行 |
| 输出文件已存在 | 自动生成 v2/v3，或要求 `--overwrite` |
| DeepSeek 调用失败 | 打印错误类型和建议检查项 |

## 13. 结构化输出

为方便 Codex 读取，建议支持 `--json` 参数。

示例：

```bash
novel polish chapters/003.md --json
```

输出：

```json
{
  "status": "ok",
  "project_root": "/path/to/my-novel",
  "mode": "polish",
  "input": "chapters/003.md",
  "output": "drafts/003.polished.md",
  "model": "deepseek-chat",
  "warnings": []
}
```

失败时：

```json
{
  "status": "error",
  "error": "Missing DEEPSEEK_API_KEY",
  "hint": "Set DEEPSEEK_API_KEY in your environment or project .env file."
}
```

## 14. `--dry-run` 设计

`--dry-run` 用于调试 prompt，不调用 DeepSeek。

示例：

```bash
novel polish chapters/003.md --dry-run --out /tmp/prompt.md
```

行为：

1. 定位项目根目录。
2. 读取项目配置和上下文。
3. 构造最终 prompt。
4. 将 prompt 输出到指定文件或打印到终端。
5. 不调用 DeepSeek。

这对调试小说风格和上下文非常重要。

## 15. AGENTS.md 示例

每个小说项目根目录建议放 `AGENTS.md`，指导 Codex 使用全局 CLI。

```markdown
# Project instructions

This is a Chinese fiction project.

Use the globally installed `novel` CLI for AI writing tasks. Do not assume the CLI source code exists inside this repository.

## Commands

- Check configuration:
  `novel config doctor`

- Polish a chapter:
  `novel polish <chapter-file>`

- Continue a chapter:
  `novel continue <chapter-file>`

- Rewrite a chapter:
  `novel rewrite <chapter-file> --instruction "<instruction>"`

- Summarize a chapter:
  `novel summarize <chapter-file>`

- Preview context:
  `novel context <chapter-file> --mode <mode>`

## Rules

- Never overwrite files in `chapters/`.
- Write generated prose to `drafts/`.
- Write summaries to `summaries/`.
- Read `novel.yaml` for project paths and context settings.
- Read `docs/style.md`, `docs/characters.md`, `docs/worldbuilding.md`, and `docs/timeline.md` when present.
- If context files are missing, continue with available context and mention what is missing.
- Prefer `novel context` before major generation tasks.
```

## 16. Skill 示例

如果后续要封装成 Codex skill，可以添加到项目中：

```text
.agents/skills/novel-deepseek/SKILL.md
```

示例：

```markdown
---
name: novel-deepseek
description: use this skill when working in a fiction project and the user asks to continue, polish, rewrite, summarize, outline, or revise novel chapters using the globally installed novel CLI and DeepSeek while preserving story continuity, character voice, timeline, and worldbuilding.
---

# Novel DeepSeek Skill

Use the globally installed `novel` command for AI writing tasks. Do not look for the CLI source code inside the novel project.

## Before generation

Prefer running:

```bash
novel config doctor
```

For major generation tasks, preview context first:

```bash
novel context <chapter-file> --mode <mode>
```

## Commands

For polishing:

```bash
novel polish <chapter-file>
```

For continuation:

```bash
novel continue <chapter-file>
```

For rewriting:

```bash
novel rewrite <chapter-file> --instruction "<user instruction>"
```

For summarizing:

```bash
novel summarize <chapter-file>
```

## Rules

- Never overwrite files in `chapters/` unless explicitly requested.
- Write generated prose to `drafts/`.
- Write summaries to `summaries/`.
- Read `novel.yaml` for project-specific paths and settings.
- Prefer `novel context` before long generation tasks.
- Report the output path and any missing context files.
```

## 17. 开发优先级

建议按阶段开发，不要一开始做得太复杂。

### 阶段 1：全局 CLI 最小可用版

实现：

```bash
novel init
novel polish chapters/003.md
novel continue chapters/003.md
novel summarize chapters/003.md
```

必备能力：

- 全局安装后可在任意目录运行。
- 能定位当前小说项目根目录。
- 能读取 `novel.yaml` 或默认目录结构。
- 能读取章节。
- 能使用项目 prompt 或内置 prompt。
- 能调用 DeepSeek。
- 默认输出到 drafts/ 或 summaries/。
- 不覆盖原文。
- 支持项目 `.env` 和系统环境变量。

### 阶段 2：增强可控性

加入：

```bash
--project
--instruction
--out
--model
--temperature
--prompt
--dry-run
--json
```

### 阶段 3：增强小说项目能力

加入：

```bash
novel context
novel rewrite
novel update-story-so-far
novel check
novel config doctor
```

### 阶段 4：接入 Codex

每个小说项目添加：

```text
AGENTS.md
.agents/skills/novel-deepseek/SKILL.md
```

## 18. 推荐实现顺序

1. 建立独立的 `novel-cli` 源码仓库。
2. 写 `pyproject.toml`，注册全局 `novel` 命令。
3. 实现 `novel init`。
4. 实现项目根目录检测逻辑。
5. 实现 `novel polish`。
6. 实现 `novel continue`。
7. 实现 `novel summarize`。
8. 添加项目 `.env`、系统环境变量和配置读取。
9. 添加项目 prompt 优先、内置 prompt 兜底的模板逻辑。
10. 添加默认输出路径和防覆盖逻辑。
11. 添加 `--instruction`、`--out`、`--dry-run`。
12. 添加 `--json`，方便 Codex 读取。
13. 添加 `novel config doctor`。
14. 编写项目模板中的 `AGENTS.md`。
15. 流程稳定后再封装 skill。

## 19. 使用示例

### 初始化小说项目

```bash
mkdir my-novel
cd my-novel
novel init
```

### 检查配置

```bash
novel config doctor
```

### 润色章节

```bash
novel polish chapters/003.md
```

### 带额外要求润色

```bash
novel polish chapters/003.md --instruction "语言更克制，减少解释性心理描写"
```

### 续写章节

```bash
novel continue chapters/003.md
```

### 指定输出路径

```bash
novel continue chapters/003.md --out drafts/003.continue.scene-a.md
```

### 指定项目根目录

```bash
novel polish chapters/003.md --project /path/to/my-novel
```

### 摘要章节

```bash
novel summarize chapters/003.md
```

### 预览上下文

```bash
novel context chapters/003.md --mode polish
```

### 只生成 prompt，不调用 API

```bash
novel polish chapters/003.md --dry-run --out drafts/003.polish.prompt.md
```

### JSON 输出

```bash
novel polish chapters/003.md --json
```

## 20. 设计原则总结

1. CLI 是全局安装的稳定执行层，不属于某一个小说项目源码。
2. 小说项目只保存项目数据、配置、提示词、设定和输出。
3. Codex 是流程编排层，不直接处理 DeepSeek API 细节。
4. 项目 prompt 模板放在 `prompts/`，方便每本小说单独调整。
5. CLI 应提供内置默认 prompt，保证新项目可以快速启动。
6. 小说设定放在 `docs/`，作为长期上下文。
7. 正式章节放在 `chapters/`，默认不可覆盖。
8. AI 输出放在 `drafts/`，摘要放在 `summaries/`。
9. API key 只放环境变量或项目 `.env`，不提交到仓库。
10. 所有命令都应有安全默认值。
11. 提供 `novel init` 初始化项目。
12. 提供 `novel config doctor` 检查环境。
13. 提供 `--dry-run` 方便调试 prompt。
14. 提供 `--json` 方便 Codex 读取执行结果。

## 21. 最终推荐形态

最终项目应形成如下使用体验：

```text
用户提出写作任务
        ↓
Codex 根据 AGENTS.md 或 skill 判断应使用全局 novel CLI
        ↓
Codex 调用 novel polish / continue / rewrite / summarize
        ↓
全局 CLI 定位当前小说项目
        ↓
CLI 读取 novel.yaml、上下文和 prompt，并调用 DeepSeek
        ↓
CLI 写入当前项目的 drafts/ 或 summaries/
        ↓
Codex 汇报输出路径、执行命令、缺失上下文和注意事项
```

这是一个清晰、可维护、可扩展的小说写作工作流。全局 CLI 负责通用能力，每个小说项目只负责保存自己的内容、设定和提示词。

