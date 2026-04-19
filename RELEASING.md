# 发布到 PyPI

以下为维护者操作说明；发布前请确保 CI（Ruff + pytest）通过，且 `CHANGELOG.md`、版本号已更新。

## 1. 版本号

同时修改并保持一致：

- `pyproject.toml` 中 `[project].version`
- `src/hdctool/version.py` 中的 `__version__`
- `CHANGELOG.md` 中对应版本小节

语义化版本建议：仅修 bug → 补丁位；新增兼容 API → 次版本；破坏性变更 → 主版本。

## 2. 本地检查

```bash
cd hdctool
pip install -e ".[dev]"
ruff check src tests
pytest
python -m build
```

`python -m build` 需要已安装 [`build`](https://pypi.org/project/build/)：`pip install build`。

## 3. 构建产物

```bash
python -m build --sdist --wheel
```

产物位于 `dist/`（`.tar.gz` 与 `.whl`）。可用 `twine check dist/*` 检查元数据。

## 4. 上传 PyPI

1. 在 [PyPI](https://pypi.org/) 与 [TestPyPI](https://test.pypi.org/) 配置 API token（推荐 trusted publishing 或 token）。
2. 安装 twine：`pip install twine`。
3. 先试测服（推荐）：

   ```bash
   twine upload --repository testpypi dist/*
   ```

4. 正式上传：

   ```bash
   twine upload dist/*
   ```

首次发包需在 PyPI 上注册项目名 `hdctool`（若已被占用则需改名）。

## 5. 发布后

- 在 Git 上打 tag：`git tag v0.3.0 && git push origin v0.3.0`（版本号替换为实际值）。
- 确认 PyPI 项目页展示说明文档与依赖正确。

## 环境说明

- **Token**：`~/.pypirc` 或 CI 密钥库中配置，勿将 token 写入仓库。
- **CI 自动发布**：可在 GitHub Actions 中于 tag 推送时用 OIDC 调用 `pypa/gh-action-pypi-publish`；具体 YAML 可按团队规范单独添加，本文不绑定单一流水线结构。
