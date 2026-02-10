以下是一份针对你描述场景的**工程化更新 & 发布流程规范（Spec）**，比较适合中小型到中大型项目（有后端 + Web + iOS 多端的情况）。

```markdown
# 项目代码更新 & 发布流程规范（Update & Deploy Spec）
最后更新：2026-xx-xx

## 核心原则

1. 任何代码变更必须可回滚、可审计、可复现
2. 尽量做到「全自动」或「极低干预」
3. 保护线上服务稳定性优先于开发效率
4. 文档永远与代码保持一致（文档即代码的一部分）

## 标准更新执行流程（Recommended Sequence）

### 0. 前置条件检查（手动或脚本强制）

- 当前分支是否为 `main` / `master` / `develop` / `release/*` 中的受保护分支？
- 本地是否有未提交的变更？（`git status --porcelain` 应为空）
- 是否已拉取最新远程代码？（`git fetch && git status` 应显示 up-to-date）

不满足以上任一点 → 终止流程并提示

### 1. 关闭所有本地已启动的服务（强制）

必须执行以下命令（建议写成一个统一脚本 `scripts/stop-all.sh`）：

```bash
# 按依赖顺序反向关闭（越底层越晚关）
pkill -f "uvicorn\|gunicorn\|python.*main.py"          # Python 后端
pkill -f "next dev\|next start\|vite\|webpack"         # Web 前端开发/构建服务
pkill -f "podman\|docker.*808[0-9]\|300[0-9]"          # 容器（可选）
# iOS 模拟器不强制关闭，但建议添加：
osascript -e 'tell application "Simulator" to quit'    # macOS only
```

建议在所有开发脚本最开头都调用此脚本。

### 2. 代码更新 / 生成完成后，必须执行的编译 & 静态检查链

按顺序执行，**任一步骤失败则整体中止**，不允许跳过。

```text
└─ backend
   ├─ poetry lock --no-update          # 或 pip-compile
   ├─ poetry install --sync            # 或 pip install -r requirements.txt
   ├─ ruff check .                     # 或 flake8 / pylint
   ├─ ruff format --check .            # 或者 black --check
   ├─ mypy .                           # 类型检查（推荐）
   └─ pytest -m "not slow"             # 单元测试 + 部分集成测试（快速组）

└─ web (next.js / vite / ...)
   ├─ pnpm install --frozen-lockfile   # 或 yarn install --immutable
   ├─ pnpm lint                        # eslint + stylelint
   ├─ pnpm typecheck                   # tsc --noEmit
   └─ pnpm build                       # next build / vite build

└─ ios (Xcode 项目)
   └─ xcodebuild -workspace xxx.xcworkspace \
                 -scheme "YourApp" \
                 -configuration Debug \
                 -destination "generic/platform=iOS Simulator" \
                 build               # 或 archive / analyze
      （可选：加 clean 前置）
```

建议把以上命令封装成一个统一入口脚本：

```bash
scripts/ci-build-and-lint.sh    # 在本地和 CI 都执行
```

### 3. 更新文档（docs/ 目录）

#### 必须更新的文件类型（至少包含以下任一变更时更新对应文档）

| 变更类型               | 建议修改的文件                              | 修改方式                     |
|-----------------------|---------------------------------------------|------------------------------|
| 新增/删除/升级依赖     | docs/dependencies.md 或 docs/backend.md     | 更新版本号、变更日期、原因   |
| Python 版本变更        | docs/technical-stack.md 或 README.md        | 全局搜索替换版本号           |
| 新增/修改 API          | docs/api/** 或 docs/openapi/                | 更新 OpenAPI / 接口说明      |
| 前端路由/页面大改      | docs/frontend-architecture.md               | 更新路由表、组件关系图       |
| iOS 最低支持版本变更   | docs/ios-requirements.md                    | 更新版本号与说明             |
| 数据文件格式变化       | docs/data-dictionary.md                     | 更新字段说明                 |

**规则**：
- 新增文档一律放在 `docs/updates/YYYY-MM/` 目录下，文件名格式：`YYYY-MM-DD-HHMM-project-module-update.md`
- 修改已有文档时，**在文件最上方**增加变更记录块（最近的放最上面）

```markdown
## 变更历史

- 2026-02-09 beiting  
  更新 Python 至 3.12 → 3.13  
  升级 sqlalchemy 2.0 → 2.1.0  
  影响模块：用户认证、订单系统
```

### 4. 自动提交 & 推送规范

在所有检查、编译、文档更新完成后，执行：

```bash
scripts/auto-commit-and-push.sh "<类型>: <简短核心描述>"
```

提交信息格式建议（参考 conventional commits）：

```
feat: 新增会员积分兑换规则后台管理
fix: 修复 iOS 端订单列表下拉刷新不触发加载
refactor: 重构用户认证模块，统一使用 OAuth2 密码模式
docs: 更新依赖版本清单及 Python 版本要求
chore: 升级 next.js 至 15.x 并修复构建警告
```

**脚本内部逻辑示例**（建议）：

```bash
#!/usr/bin/env bash
set -euo pipefail

MSG=${1:-"chore: auto update after build & doc sync"}

git add .
git commit -m "$MSG" || echo "Nothing to commit"
git push origin HEAD || echo "Already up-to-date"
```

### 5. 代码 & 文件存放规范（强制）

| 文件类型           | 存放目录              | 备注                                      |
|---------------------|-----------------------|-------------------------------------------|
| 功能说明、使用文档 | `docs/`               | 所有对外/对内说明文档                     |
| 更新日志类文档     | `docs/updates/YYYY-MM/` | 按月分目录，方便后续归档                  |
| 单元测试 / E2E 测试| `tests/`              | 尽量按模块/功能分目录                      |
| 测试用数据文件     | `data/` 或 `tests/data/` | json、csv、图片、mock 响应等               |
| 临时脚本、工具     | `scripts/`            | stop-all、ci-build、auto-commit 等         |
| CI 配置文件        | `.github/workflows/`  | GitHub Actions 或其他 CI 配置              |

## 快速检查清单（贴在桌面或 IDE 启动页）

- [ ] 已执行 `stop-all.sh`
- [ ] `scripts/ci-build-and-lint.sh` 全绿
- [ ] 文档已更新或新增到 `docs/updates/`
- [ ] 提交信息符合规范
- [ ] 已 push

祝开发愉快，线上稳定 ✌️
```

这份规范可以根据你们团队实际使用的技术栈（poetry/uv/pnpm/yarn、eslint/ruff、next/vite、xcodebuild 等）再做细化。

需要我帮你把某个部分再展开成可直接执行的 bash / python 脚本吗？（例如 stop-all、auto-commit、文档变更记录生成等）

