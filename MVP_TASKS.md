# Novel CLI MVP Tasks

## Phase 1 MVP

- [x] 重整工程为 `novel_cli/` 包结构，并暴露全局命令 `novel`
- [x] 更新 `pyproject.toml`，补齐 `openai`、`python-dotenv`、`pyyaml` 依赖
- [x] 实现 `novel init`
- [x] 实现项目根目录自动检测
- [x] 实现 `novel.yaml` 和项目 `.env` 读取
- [x] 实现 `novel polish`
- [x] 实现 `novel continue`
- [x] 实现 `novel summarize`
- [x] 实现项目 prompt 优先、内置 prompt 兜底
- [x] 实现默认输出路径和版本号递增防覆盖
- [x] 实现 DeepSeek 客户端封装和清晰错误提示
- [x] 补齐内置模板和 `novel init` 生成模板
- [x] 为 happy path、错误路径、模板回退和输出版本化补测试

## Deferred

- [ ] `novel rewrite`
- [ ] `novel context`
- [ ] `novel config doctor`
- [ ] `--project`
- [ ] `--instruction`
- [ ] `--out`
- [ ] `--model`
- [ ] `--temperature`
- [ ] `--prompt`
- [ ] `--dry-run`
- [ ] `--json`
- [ ] `--overwrite`
- [ ] 用户级全局配置
- [ ] Codex skill 集成
