# 发布检查清单（Release Checklist）

> 每次发布前必须逐项执行，不能跳过。
> 构建日志中的每条 warning / error 都必须记录在发布报告中。

## 一、版本号

- [ ] `pyproject.toml` 中 `version` 已更新
- [ ] `src/stockhub_mcp/__init__.py` 中 `__version__` 已更新
- [ ] 已执行 `pip index versions stockhub-mcp` 确认版本不与 PyPI 已发布版本冲突
- [ ] `CHANGELOG.md` 已补充当前版本条目

## 二、元数据与文件完整性

- [ ] `pyproject.toml` 字段格式合规
  - [ ] `license` 使用 SPDX 字符串（如 `"MIT"`），不能是 `{text = "MIT"}` dict 格式
  - [ ] `classifiers` 不含已废弃项（如 `License :: OSI Approved :: MIT License`）
  - [ ] `requires-python` 与实际测试的 Python 版本一致
- [ ] 项目根目录必备文件存在
  - [ ] `LICENSE` 文件（`pyproject.toml` 中声明的 license 必须有对应文件）
  - [ ] `README.md`
  - [ ] `CHANGELOG.md`
  - [ ] `.gitignore`（至少排除 `dist/`、`*.egg-info/`、`__pycache__/`、`.venv/`）
- [ ] `.gitignore` 已排除内部文件
  - [ ] `overview.md`（工作区临时文件，不得进入版本库和发布包）
  - [ ] `dist/`
  - [ ] `*.egg-info/`

## 三、构建前校验

- [ ] `git status` 确认无意外未提交改动
- [ ] `git status` 确认无意外未跟踪文件（`??`），如有则判断是否该加入 `.gitignore`
- [ ] `dist/` 已清空（`rm -rf dist src/stockhub_mcp.egg-info`）
- [ ] 构建依赖可用（`pip install build twine`）
- [ ] 当前 `pip install -e .` 安装态能正常 `import stockhub_mcp`

## 四、构建

- [ ] `python -m build` 构建成功，无 error
- [ ] 逐行检查构建 stdout/stderr：
  - [ ] 无 `ERROR`
  - [ ] 每条 `DeprecationWarning` / `UserWarning` 已记录到发布报告
  - [ ] 无未知 Warning 被忽略

## 五、产物质量

- [ ] `dist/` 中存在 `.whl` 和 `.tar.gz`
- [ ] sdist 内容检查（`tar -tzf dist/stockhub_mcp-*.tar.gz`）：
  - [ ] 包含 `README.md`
  - [ ] 包含 `LICENSE`
  - [ ] 包含 `CHANGELOG.md`
  - [ ] 包含 `pyproject.toml`
  - [ ] 包含完整源码目录 `src/stockhub_mcp/`
  - [ ] 不包含 `overview.md`、`.workbuddy/`、`__pycache__/`
- [ ] wheel 内容检查（`python -m zipfile --list dist/*.whl`）：
  - [ ] 只包含 `stockhub_mcp/` 和 `.dist-info/`，不含测试文件、文档文件、内部工具文件
  - [ ] 不包含 `tests/` 目录
  - [ ] 不包含 `docs/` 目录
  - [ ] 不包含 `overview.md`
- [ ] 本地安装验证：`pip install dist/stockhub_mcp-*-py3-none-any.whl --force-reinstall` 无报错
- [ ] 安装后 `python -c "import stockhub_mcp; print(stockhub_mcp.__version__)"` 输出版本号正确
- [ ] 安装后 `fastmcp run -m stockhub_mcp.server` 能正常拉起 MCP 服务（至少不报 import 错误）

## 六、上传

- [ ] `twine upload dist/*` 上传成功
- [ ] PyPI 页面可正常访问（`https://pypi.org/project/stockhub-mcp/<version>/`）
- [ ] `pip install stockhub-mcp==<新版本>` 能从 PyPI 正常获取并安装
- [ ] 安装后再次验证 `python -c "import stockhub_mcp; print(stockhub_mcp.__version__)"`

## 七、发布报告（书面，不可口头）

发布报告必须包含以下所有条目，缺一不可：

- [ ] 版本号和一句话改动范围说明
- [ ] 构建输出中每条 warning 的原文、严重性评估、处理决定（修复 / 本次容忍/原因 / 下次必须处理）
- [ ] `git diff --stat <上一版本>..HEAD` 改动概览
- [ ] 产物清单（wheel 路径、sdist 路径、文件数、大小）
- [ ] sdist 内容抽样验证结果
- [ ] wheel 内容抽样验证结果
- [ ] 本地安装验证结果
- [ ] PyPI 安装验证结果
