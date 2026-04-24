# novel-cli

一个面向小说项目的全局 CLI，负责读取项目上下文、拼接 prompt、调用 OpenAI-compatible API，并把结果安全地写回项目目录。

当前版本是阶段 1 MVP，已实现：

- `novel init`
- `novel init-config`
- `novel polish <chapter-file>`
- `novel continue <chapter-file>`
- `novel summarize <chapter-file>`

## Requirements

- Python `>=3.10`
- OpenAI-compatible API key

## Install

推荐使用 `pipx` 全局安装：

```bash
pipx install /path/to/novel-cli
```

开发阶段可以用可编辑安装：

```bash
pipx install -e /path/to/novel-cli
```

如果只是在仓库里本地开发，也可以：

```bash
pip install -e .
```

安装后可直接使用：

```bash
novel --help
novel init-config
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

为项目配置 API key，最少只需要：

```env
NOVEL_API_KEY=your_api_key_here
```

如果你要覆盖默认接口和模型，也可以在项目 `.env` 中补充：

```env
NOVEL_API_KEY=your_api_key_here
NOVEL_BASE_URL=https://api.openai.com/v1
NOVEL_MODEL=gpt-4.1-mini
NOVEL_TEMPERATURE=0.7
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

### `novel init-config`

在用户级配置目录生成 `config.yaml`，只写非敏感默认项，不覆盖已有文件。

示例：

```bash
novel init-config
```

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

当前版本支持三类配置来源：

- 用户级配置文件
- 项目根目录的 `novel.yaml`
- 项目 `.env` 与系统环境变量

用户级配置路径：

- Windows: `%APPDATA%\novel-cli\config.yaml`
- macOS: `~/Library/Application Support/novel-cli/config.yaml`
- Linux: `~/.config/novel-cli/config.yaml`

可以先执行：

```bash
novel init-config
```

生成默认配置：

```yaml
api:
  base_url: https://api.openai.com/v1

model:
  name: gpt-4.1-mini
  temperature: 0.7
```

API key 仍然只通过环境变量或项目 `.env` 提供，不写入配置文件。

`novel.yaml` 示例：

```yaml
project_name: my-novel
language: zh-CN

api:
  base_url: https://api.openai.com/v1

model:
  name: gpt-4.1-mini
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

配置优先级：

- `NOVEL_API_KEY` 只来自环境变量或项目 `.env`，必须存在
- `NOVEL_BASE_URL` 环境变量 > 项目 `api.base_url` > 用户级 `api.base_url` > `https://api.openai.com/v1`
- `NOVEL_MODEL` 环境变量 > 项目 `model.name` > 用户级 `model.name` > `gpt-4.1-mini`
- `NOVEL_TEMPERATURE` 环境变量 > 项目 `model.temperature` > 用户级 `model.temperature` > `0.7`

旧的用户级配置键和包含 `provider` 的项目配置不会被自动兼容，CLI 会直接报迁移错误。

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

当前仓库包含命令流程、配置读取、模板回退、输出版本化、配置迁移错误和元数据断言测试。

如果要做全局安装 smoke test，推荐：

```bash
pipx install -e .
novel --help
novel init-config
```

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
