# 架构设计

本文档描述 `novel-cli` 的内部设计——模块职责、数据流与设计原则。

## 总览

`novel-cli` 是一个全局安装的 Python CLI，将 OpenAI 兼容 API 调用封装为小说写作命令。它不嵌入任何一个小说项目，而是跨所有项目通用。

架构分为三层：

```text
用户 / AI 代理
       │
       │ novel polish chapters/003.md
       ▼
全局 novel CLI ── 稳定执行层
  • 解析命令、定位项目根目录
  • 读取配置与上下文
  • 构建 prompt、调用 API
  • 安全写入输出
       │
       ▼
小说项目目录 ── 数据与配置
  • 章节、草稿、摘要
  • prompt、设定文档
  • novel.yaml、.env
```

## 模块地图

```text
novel_cli/
  __init__.py              # 版本号 (0.1.0)
  cli.py                   # argparse 入口，命令分发
  config.py                # 配置 dataclass + 三层合并逻辑
  api_client.py            # OpenAI SDK 封装
  project_detector.py      # 定位项目根目录
  project_initializer.py   # novel init — 从模板生成项目骨架
  context_loader.py        # 读取章节 + 可选的上下文文件
  prompt_builder.py        # 加载模板、变量替换
  file_utils.py            # 输出路径 + 版本化命名
  output.py                # 终端输出格式化
  errors.py                # NovelCliError 数据类

  templates/
    prompts/               # 内置兜底 prompt 模板
      polish.md
      continue.md
      summarize.md
    project/               # novel init 用的项目模板
      novel.yaml
      AGENTS.md
      .gitignore
      docs/                # 空白起始上下文文件
      prompts/             # 起始 prompt 模板
      summaries/
```

## 数据流

```
novel polish chapters/003.md
                │
                ▼
         cli.py ── 解析参数，分发到 "polish" 处理
                │
                ▼
    project_detector.py ── 定位项目根目录
                │
                ▼
         config.py ── 加载并合并三层配置
                │
                ▼
     context_loader.py ── 读取章节 + 所有可选的上下文文件
                │
                ▼
     prompt_builder.py ── 解析模板（项目 → 内置回退）
                │          替换 {{变量}}
                ▼
      api_client.py ── POST 到 /v1/chat/completions
                │
                ▼
       file_utils.py ── 确定输出路径，处理版本化
                │
                ▼
         output.py ── 打印结果摘要到终端
```

## 模块职责

### `cli.py`
入口模块。用 argparse 设置子命令（`init`、`init-config`、`polish`、`continue`、`summarize`）。解析项目根目录和配置后分发给对应处理函数。

### `config.py`
定义数据类：`ProjectConfig`、`UserConfig`，以及三层配置合并辅助函数。同时负责校验和拒绝旧配置键。读取 `novel.yaml`、用户级 `config.yaml` 和 `.env`。

### `api_client.py`
封装 OpenAI Python SDK。接收 prompt 字符串、base URL、模型名、温度和可选的 system prompt。返回纯文本响应。处理缺少 API key、网络错误和 API 错误，报出清晰错误信息。

### `project_detector.py`
从当前工作目录向上遍历，查找 `novel.yaml`。回退方案：检查当前目录是否含 `chapters/`。返回项目根目录路径或抛出 `NovelCliError`。

### `project_initializer.py`
实现 `novel init`。从 `templates/project/` 复制模板文件到当前目录。已存在的文件会被跳过，不会覆盖用户内容。

### `context_loader.py`
读取目标章节文件，并根据 `novel.yaml` 中的路径选择性地读取上下文文件。可选文件缺失时输出 warning，不中断执行。

### `prompt_builder.py`
为给定模式解析 prompt 模板：先检查项目特定模板（如 `prompts/polish.md`），不存在则回退到内置模板。将模板变量替换为实际内容。

### `file_utils.py`
根据模式和章节名确定输出文件路径。目标文件已存在时处理版本化命名（如 `001.polished.v2.md`）。

### `output.py`
格式化终端输出：初始化摘要、生成结果摘要（输入、输出、模型、警告）和错误信息。

### `errors.py`
定义 `NovelCliError`——包含 `message` 字符串和可选 `hint` 字符串的数据类。

## 设计原则

1. **CLI 是全局的，而非项目内嵌。** 一次安装，所有小说项目通用。
2. **项目自持数据。** CLI 只对项目目录读写，不维护自身状态。
3. **默认安全。** 绝不覆盖 `chapters/`。输出到 `drafts/` 和 `summaries/`。
4. **优雅降级。** 缺失可选上下文文件产生 warning 而非 error。
5. **Prompt 模板可定制。** 项目模板覆盖内置默认值，做到每本书独立调校。
6. **API key 隔离。** key 只来自环境变量或 `.env`——不写入任何 YAML 配置文件。

## 打包布局

包使用 `setuptools` 作为构建后端，配以 `pyproject.toml`（PEP 621）。控制台入口点 `novel` 映射到 `novel_cli.cli:main`。

模板和项目脚手架文件在 `[tool.setuptools.package-data]` 中声明为包数据，通过 `importlib.resources` 加载。

## 测试

测试在 `tests/` 中，使用 pytest。测试隔离通过 `conftest.py` 的 `workspace_dir` fixture 创建临时目录实现。关于运行和编写测试的细节见 [contributing.md](contributing.md)。

## 路线图

### 阶段 1 — MVP（当前）
- [x] `novel init`、`init-config`
- [x] `novel polish`、`continue`、`summarize`
- [x] 三层配置、项目定位、模板解析
- [x] 安全输出与版本化

### 阶段 2 — 增强可控性
- [ ] `--instruction`、`--out`、`--model`、`--temperature`
- [ ] `--prompt`、`--dry-run`、`--json`、`--overwrite`
- [ ] `--project`

### 阶段 3 — 扩展命令
- [ ] `novel rewrite`
- [ ] `novel context`
- [ ] `novel config doctor`
- [ ] `novel update-story-so-far`

### 阶段 4 — 代理集成
- [ ] AGENTS.md 和 skill 封装，对接 AI 代理工作流
