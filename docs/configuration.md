# 配置参考

`novel-cli` 从四处来源组合运行时配置。本文档涵盖每个配置项、优先级以及如何配置。

## 配置层级

优先级从高到低：

| 层级 | 来源 | 说明 |
|---|---|---|
| 1（最高） | 命令行参数 | 一次性覆盖，如 `--project`、`--model`、`--temperature` |
| 2 | 环境变量 / 项目 `.env` | 运行时覆盖；API key 仅在此层 |
| 3 | 项目 `novel.yaml` | 每个项目独立设置 |
| 4（最低） | 用户级 `config.yaml` | 跨所有项目的全局默认值 |

当所有层都未提供某个值时，使用内置硬编码默认值。

## 环境变量

| 变量 | 用途 | 示例 |
|---|---|---|
| `NOVEL_API_KEY` | API key（**必填**） | `sk-...` |
| `NOVEL_BASE_URL` | API 接口地址 | `https://api.openai.com/v1` |
| `NOVEL_MODEL` | 模型名称 | `gpt-4.1-mini` |
| `NOVEL_TEMPERATURE` | 采样温度（0–2） | `0.7` |

环境变量优先于项目配置和用户配置，但低于命令行参数。可在系统全局设置，也可写入项目 `.env` 文件（由 `python-dotenv` 加载）。

`.env` 文件放在项目根目录，且必须列入 `.gitignore`：

```gitignore
.env
```

## 用户级配置

各平台配置路径：

| 平台 | 路径 |
|---|---|
| Windows | `%APPDATA%\novel-cli\config.yaml` |
| macOS | `~/Library/Application Support/novel-cli/config.yaml` |
| Linux | `~/.config/novel-cli/config.yaml` |

生成命令：

```bash
novel init-config
```

默认内容：

```yaml
api:
  base_url: https://api.openai.com/v1

model:
  name: gpt-4.1-mini
  temperature: 0.7
```

用户级配置**绝不存储 API key**，key 只来自环境变量。

## 项目配置（`novel.yaml`）

放在项目根目录。完整结构：

```yaml
project_name: my-novel      # 项目名称
language: zh-CN             # 语言代码

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

### 字段参考

#### `api`
| 键 | 必填 | 说明 |
|---|---|---|
| `base_url` | 否 | OpenAI 兼容 API 接口地址 |

#### `model`
| 键 | 必填 | 说明 |
|---|---|---|
| `name` | 否 | 发送给 API 的模型标识 |
| `temperature` | 否 | 采样温度（0–2） |

#### `paths`
| 键 | 默认值 | 说明 |
|---|---|---|
| `chapters` | `chapters` | 章节目录 |
| `drafts` | `drafts` | AI 生成正文输出目录 |
| `summaries` | `summaries` | 摘要输出目录 |
| `prompts` | `prompts` | 自定义 prompt 模板目录 |
| `docs` | `docs` | 故事设定文件目录 |

#### `context`
将每个上下文槽位映射到文件路径（相对于项目根目录）。所有条目均可选。文件缺失时 CLI 输出 warning 并继续。

#### `output`
| 键 | 默认值 | 说明 |
|---|---|---|
| `overwrite` | `false` | 为 `false` 时，已存在的输出文件自动追加版本号（v2, v3, …） |

## 优先级细则

各配置项的生效顺序：

| 配置项 | 覆盖规则 |
|---|---|
| API key | `NOVEL_API_KEY` —— **必须**来自环境变量或 `.env` |
| Base URL | `NOVEL_BASE_URL` > 项目 `api.base_url` > 用户 `api.base_url` > `https://api.openai.com/v1` |
| Model | `--model` > `NOVEL_MODEL` > 项目 `model.name` > 用户 `model.name` > `gpt-4.1-mini` |
| Temperature | `--temperature` > `NOVEL_TEMPERATURE` > 项目 `model.temperature` > 用户 `model.temperature` > `0.7` |
| Output overwrite | `--overwrite` > 项目 `output.overwrite` > `false` |

## 常用命令行覆盖

以下参数不会修改任何配置文件，只影响当前一次执行：

- `--project <路径>`：显式指定项目根目录
- `--instruction <文本>`：注入 `{{INSTRUCTION}}`
- `--out <路径>`：指定输出文件
- `--model <名称>`：覆盖模型
- `--temperature <浮点数>`：覆盖温度
- `--prompt <路径>`：显式指定 prompt 模板
- `--dry-run`：只生成 prompt，不调用 API
- `--json`：输出 JSON 结果
- `--overwrite`：覆盖目标输出文件

## 项目定位

执行命令时，CLI 按以下顺序定位项目根目录：

1. 从当前目录向上查找 `novel.yaml`
2. 若未找到，检查当前目录是否存在 `chapters/` 子目录
3. 否则报错并提示先执行 `novel init`

也可通过 `--project <路径>` 手动指定项目根目录。

## 旧配置迁移

旧的配置键（`provider`、`deepseek`）会被明确拒绝，CLI 会抛出错误并指向当前配置格式。
