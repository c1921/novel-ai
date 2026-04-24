# novel-cli

一个全局安装的小说写作 CLI，对接任意 OpenAI 兼容 API。

润色、续写、摘要你的章节——自动读取项目中的风格指南、人物设定、世界观和时间线，作为上下文参与生成。

## 环境要求

- Python `>=3.10`
- 一个 OpenAI 兼容的 API key

## 安装

```bash
# 推荐：全局安装
pipx install /path/to/novel-cli

# 或者本地可编辑安装
pip install -e .
```

验证安装：

```bash
novel --help
```

## 快速开始

### 1. 创建小说项目

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
  novel.yaml          # 项目配置
  prompts/            # 自定义 prompt 模板
  docs/               # 风格、人物、世界观等设定文件
  chapters/           # 存放章节正文
  drafts/             # AI 生成稿输出
  summaries/          # 章节摘要
```

### 2. 配置 API key

在项目根目录创建 `.env` 文件：

```env
NOVEL_API_KEY=你的_API_key
```

可选：覆盖默认的 API 接口和模型：

```env
NOVEL_BASE_URL=https://api.openai.com/v1
NOVEL_MODEL=gpt-4.1-mini
NOVEL_TEMPERATURE=0.7
```

### 3. 开始写作

把第一章放到 `chapters/001.md`，然后：

```bash
# 润色章节（优化文笔，不改变剧情）
novel polish chapters/001.md

# 从章节结尾继续写作
novel continue chapters/001.md

# 生成章节摘要
novel summarize chapters/001.md
```

生成结果写入 `drafts/`（正文）或 `summaries/`（摘要），**绝对不会覆盖** `chapters/` 中的原文。

## 命令

| 命令 | 作用 | 默认输出位置 |
|---|---|---|
| `novel init` | 在当前目录生成小说项目模板 | — |
| `novel init-config` | 创建用户级默认配置（API 接口、模型） | — |
| `novel polish <文件>` | 润色章节，不改变剧情 | `drafts/<章节名>.polished.md` |
| `novel continue <文件>` | 从章节结尾续写正文 | `drafts/<章节名>.continued.md` |
| `novel summarize <文件>` | 生成结构化章节摘要 | `summaries/<章节名>.md` |

## 项目结构

一个完整的小说项目目录如下：

```text
my-novel/
  novel.yaml              # 项目设置和上下文文件路径
  .env                    # API key（不可提交）
  .gitignore
  AGENTS.md               # AI 代理指引

  chapters/               # 章节原文（CLI 只读）
    001.md
    002.md

  drafts/                 # AI 生成的正文
    001.polished.md
    001.continued.md

  summaries/              # AI 生成的摘要
    001.md
    story-so-far.md

  prompts/                # 自定义 prompt 模板（缺则回退内置）
    polish.md
    continue.md
    summarize.md

  docs/                   # 故事设定参考
    style.md              # 文风指南
    characters.md         # 人物设定与关系
    worldbuilding.md      # 世界观、规则、阵营
    timeline.md           # 事件时间线
    glossary.md           # 专有名词对照
```

## 上下文文件

CLI 在构造 prompt 时会自动读取以下文件，让 AI 全面了解你的故事：

| 文件 | 内容 |
|---|---|
| `docs/style.md` | 文风、叙事节奏、禁忌表达 |
| `docs/characters.md` | 人物设定、关系、说话方式 |
| `docs/worldbuilding.md` | 世界观、地点、阵营 |
| `docs/timeline.md` | 事件顺序和时间线 |
| `docs/glossary.md` | 专有名词参考 |
| `summaries/story-so-far.md` | 前情摘要 |

缺失的上下文文件只会产生 warning，不会中断命令执行。

## 自定义 Prompt 模板

在 `prompts/` 中创建你自己的 prompt 模板，定制 AI 的行为方式。支持的模板变量：

- `{{CHAPTER_TEXT}}` — 章节正文
- `{{STYLE_GUIDE}}` — `docs/style.md` 的内容
- `{{CHARACTERS}}` — `docs/characters.md` 的内容
- `{{WORLDBUILDING}}` — `docs/worldbuilding.md` 的内容
- `{{TIMELINE}}` — `docs/timeline.md` 的内容
- `{{GLOSSARY}}` — `docs/glossary.md` 的内容
- `{{STORY_SO_FAR}}` — `summaries/story-so-far.md` 的内容
- `{{INSTRUCTION}}` — 用户额外指令（已预留，CLI 参数尚未开放）

如果某个 prompt 文件缺失，CLI 会自动回退到内置默认模板。

## 输出规则

- **永不覆盖** `chapters/` 中的原文
- 正文输出到 `drafts/`，摘要输出到 `summaries/`
- 目标文件已存在时自动增加版本号：`001.polished.md` → `001.polished.v2.md` → `001.polished.v3.md`

## 配置

`novel-cli` 使用三层配置，优先级从高到低：

1. **环境变量** / 项目 `.env` 文件
2. **项目级** `novel.yaml`
3. **用户级** `~/.config/novel-cli/config.yaml`

API key **只能**通过 `NOVEL_API_KEY` 环境变量或项目 `.env` 设置——不会写入任何配置文件。

一次性设置用户级默认值（API 接口、模型、温度）：

```bash
novel init-config
```

完整的配置参考见 [docs/configuration.md](docs/configuration.md)。

## 延伸阅读

- [配置参考](docs/configuration.md) — 所有配置项、优先级与环境变量
- [架构设计](docs/architecture.md) — 模块设计、数据流、设计原则
- [贡献指南](docs/contributing.md) — 开发环境、测试、代码规范
