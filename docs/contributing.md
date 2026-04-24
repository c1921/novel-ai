# 贡献指南

如何搭建开发环境、运行测试、以及为 `novel-cli` 添加新功能。

## 开发环境搭建

```bash
# 克隆仓库
git clone <仓库地址> novel-cli
cd novel-cli

# 创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows 上为 .venv\Scripts\activate

# 可编辑安装，包含测试依赖
pip install -e ".[test]"
```

验证：

```bash
novel --help
```

## 项目结构

```text
novel-cli/
  novel_cli/          # 主包
    templates/        # 内置 prompt 与项目模板
  tests/              # pytest 测试套件
  docs/               # 开发者文档
  pyproject.toml      # 构建配置与依赖
```

## 运行测试

```bash
# 运行全部测试
pytest tests

# 详细输出
pytest tests -v

# 运行单个文件
pytest tests/test_config.py -v
```

测试使用临时目录（`conftest.py` 中的 `workspace_dir` fixture）——测试不会接触你的实际文件系统。

## 测试覆盖

| 文件 | 覆盖内容 |
|---|---|
| `test_cli.py` | 命令调用：init、init-config、rewrite/context/config doctor、dry-run/json、输出版本化、配置优先级、错误场景 |
| `test_config.py` | 配置加载：默认值、YAML 读取、环境变量优先级、用户配置回退、项目优先用户、旧键拒绝 |
| `test_api_client.py` | 缺少 API key 的错误 |
| `test_file_utils.py` | 输出版本化（v2 → v3） |
| `test_project_detector.py` | 嵌套目录定位、`chapters/` 回退、失败场景 |
| `test_prompt_builder.py` | 项目模板优先、内置回退、模板缺失错误 |
| `test_packaging_metadata.py` | 包数据完整性、文件命名正确性、无残留旧代码 |

## 添加新命令

1. **添加处理函数** 到新模块或已有模块（如一个 `rewrite` 函数）。
2. **注册子命令** 在 `cli.py` 中——添加子解析器和参数。
3. **创建内置 prompt 模板** 在 `novel_cli/templates/prompts/` 中（如果该命令需要调用 API）。
4. **将模板文件** 添加到 `MANIFEST.in` 和 `pyproject.toml` 的 `[tool.setuptools.package-data]` 中。
5. **编写测试** 在 `tests/` 中。
6. **更新** `docs/architecture.md`（模块职责）和 `README.md`（命令表）。

## 添加新模板变量

1. 在 `prompt_builder.py` 的替换字典中添加变量。
2. 确保 `context_loader.py` 中加载了对应数据。
3. 在 `README.md`（模板变量部分）中记录新变量。
4. 在 `test_prompt_builder.py` 中添加覆盖该变量的测试。

## 代码规范

- **Python 3.10+**，使用 `from __future__ import annotations` 支持前向引用
- **dataclasses**（slotted）定义数据结构
- **argparse** 处理 CLI——不使用第三方 CLI 框架
- `api_client.py` 同时支持阻塞式返回和流式 token 输出
- **`importlib.resources`** 加载包数据（模板）
- **`platformdirs`** 处理跨平台配置路径
- 模块职责单一：每个文件一个清晰的职责

## 构建与打包

```bash
# 构建 wheel
python -m build

# 从构建好的 wheel 安装
pipx install dist/novel_cli-0.1.0-py3-none-any.whl
```

`pyproject.toml` 中注册的控制台入口点：

```toml
[project.scripts]
novel = "novel_cli.cli:main"
```

## 提交前检查

- [ ] 全部测试通过：`pytest tests -v`
- [ ] 无残留或注释掉的代码
- [ ] 新功能有测试覆盖
- [ ] 相关文档已更新
- [ ] `novel --help` 输出保持清晰
