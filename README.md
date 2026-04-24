# novel-cli

一个面向小说项目的全局 CLI，负责读取项目上下文、拼接 prompt、调用 DeepSeek，并把结果安全地写回项目目录。

当前版本是阶段 1 MVP，已实现：

- `novel init`
- `novel polish <chapter-file>`
- `novel continue <chapter-file>`
- `novel summarize <chapter-file>`

## Requirements

- Python `>=3.10`
- DeepSeek API Key

## Install

开发安装：

```bash
pip install -e .
```

安装后可直接使用：

```bash
novel --help
```

## Quick Start

初始化一个小说项目：

```bash
mkdir my-novel
cd my-novel
novel init
```

生成的基础结构：

```text
my-novel/
  .gitignore
  AGENTS.md
  novel.yaml
  prompts/
  docs/
  chapters/
  drafts/
  summaries/
```

为项目配置 API Key：

```env
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

把第一章放到 `chapters/001.md` 后，就可以执行：

```bash
novel polish chapters/001.md
novel continue chapters/001.md
novel summarize chapters/001.md
```

## Commands

### `novel init`

在当前目录生成小说项目模板，不覆盖已有文件。

### `novel polish <chapter-file>`

读取章节与项目上下文，生成润色稿，默认输出到：

```text
drafts/<chapter>.polished.md
```

### `novel continue <chapter-file>`

从章节结尾继续写作，默认输出到：

```text
drafts/<chapter>.continued.md
```

### `novel summarize <chapter-file>`

生成章节摘要，默认输出到：

```text
summaries/<chapter>.md
```

## Project Detection

CLI 按以下顺序定位项目根目录：

1. 从当前目录向上查找 `novel.yaml`
2. 如果没找到，但当前目录存在 `chapters/`，则使用当前目录
3. 否则报错并提示先运行 `novel init`

## Configuration

当前 MVP 支持两类配置来源：

- 项目根目录的 `novel.yaml`
- 项目 `.env` 与系统环境变量

`novel.yaml` 示例：

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
```

## Prompt Resolution

每个生成命令会优先读取项目模板：

```text
prompts/polish.md
prompts/continue.md
prompts/summarize.md
```

如果项目模板不存在，会自动回退到 CLI 内置模板。

当前支持的模板变量：

- `{{CHAPTER_TEXT}}`
- `{{STYLE_GUIDE}}`
- `{{CHARACTERS}}`
- `{{WORLDBUILDING}}`
- `{{TIMELINE}}`
- `{{GLOSSARY}}`
- `{{STORY_SO_FAR}}`
- `{{INSTRUCTION}}`

其中 `INSTRUCTION` 在当前 MVP 中固定为空，相关命令参数还未开放。

## Output Rules

- 不会覆盖 `chapters/` 下的原文
- 生成正文默认写入 `drafts/`
- 章节摘要默认写入 `summaries/`
- 如果目标文件已存在，会自动生成版本号

例如：

```text
drafts/001.polished.md
drafts/001.polished.v2.md
drafts/001.polished.v3.md
```

## Context Files

这些文件会在存在时自动参与 prompt 构造：

- `docs/style.md`
- `docs/characters.md`
- `docs/worldbuilding.md`
- `docs/timeline.md`
- `docs/glossary.md`
- `summaries/story-so-far.md`

它们缺失时不会中断命令，只会输出 warning。

## Testing

运行测试：

```bash
pytest tests
```

当前仓库包含命令流程、配置读取、模板回退、输出版本化和错误路径测试。

## Current MVP Boundary

下面这些能力还没有实现：

- `novel rewrite`
- `novel context`
- `novel config doctor`
- `--project`
- `--instruction`
- `--out`
- `--model`
- `--temperature`
- `--prompt`
- `--dry-run`
- `--json`
- `--overwrite`
- 用户级全局配置
