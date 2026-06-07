# Stage 02 · 前端工程化（ESLint + Prettier + Husky + lint-staged）

| 项目 | 内容 |
|---|---|
| 日期 | 2026-05-23 |
| 范围 | 给 `web/` 补齐 lint / format / git pre-commit 全套工具链 |
| 状态 | 代码已交付（4 个新增配置 + 4 个修改 + 1 个 hook 模板）；`git init` / `pnpm install` / `pnpm format` / `pnpm lint` 在 shell 执行 |

---

## 1. 背景与目标

Stage 01 把基础聊天跑通了，但 `web/` 还没有任何 lint / format / git hook 工具链。随着后续阶段（工具调用、文件操作、多 Agent UI）代码量增长，需要：

- **统一代码风格**（避免 PR 里 100 行 diff 全是引号风格）
- **本地即时反馈**（编辑器里就能看到错误，不用等 CI）
- **提交时强制兜底**（漏跑 lint 的代码进不去仓库）

**不做**：CI 配置、commitlint / conventional commits、tsc 在 hook 内运行（会拖慢提交体验）、后端 Python 工具链（留给 Stage 03 或其它）。

---

## 2. 技术决策

| 项 | 选择 | 理由 |
|---|---|---|
| Lint | **ESLint v9 (flat config)** | v9 是 2024 起的默认，flat config 是未来；旧 `.eslintrc` 已被 ESLint 官方 deprecate |
| TS lint | **typescript-eslint v8**（统一包） | 官方推荐入口，省去手动装 `@typescript-eslint/{parser,eslint-plugin}` |
| React 规则 | `eslint-plugin-react` + `eslint-plugin-react-hooks` + `eslint-plugin-react-refresh` | Vite + React 标准三件套，`react-refresh` 防止 fast refresh 失效 |
| Format | **Prettier v3** | 行业默认，零争论 |
| ESLint × Prettier | `eslint-config-prettier`（仅关冲突规则） | 不用 `eslint-plugin-prettier`：让两者分开跑更快、报错更清晰，2025 起社区共识 |
| Git hook | **Husky v9** | v9 极简（无需 `husky install` shell 头），与 monorepo 友好 |
| 增量检查 | **lint-staged v15** | 只跑改动文件，3 秒级 |
| Pre-commit 内容 | `eslint --fix` + `prettier --write` | 用户明确确认；**不**跑 tsc（30 秒级会让人想 `--no-verify`） |
| Pre-commit 触发的 commit msg 检查 | 无 | 用户明确不要 |
| Git 仓库 | 项目根 `git init`（若尚未） | husky 必须在 git 仓库内才能挂 hook |
| Husky 安装位置 | `web/.husky/`，hooksPath 指向它 | 子目录自治；不需要给根加 `package.json` |

---

## 3. 目录变更

新增（5 个文件）
```
web/eslint.config.js              # ★ ESLint v9 flat config
web/.prettierrc.json              # Prettier 配置
web/.prettierignore               # Prettier 忽略
web/scripts/husky-pre-commit.sh   # pre-commit hook 模板（prepare 会复制到 .husky/pre-commit）
```

> 设计变更：原计划直接落地 `web/.husky/pre-commit`。实际把 hook 内容存为 `scripts/husky-pre-commit.sh`，让 `prepare` 生命周期脚本在 `pnpm install` 时 `husky && cp scripts/husky-pre-commit.sh .husky/pre-commit && chmod +x`。好处：仓库里只保留模板（单一来源），`.husky/` 完全由 husky 自管，重装 / 切换分支 / clone 后一次 `pnpm install` 即可恢复 hook，不需要手动写 `.husky/`。

修改（4 个文件）
```
web/package.json                  # devDeps + scripts + lint-staged 配置
web/.gitignore                    # 加 .eslintcache
docs/README.md                    # 加 Stage 02 索引
web/README.md                     # 加 lint/format/typecheck 命令
```

文档新增
```
docs/stage-02-frontend-tooling.md # 本文
```

---

## 4. 关键设计

### 4.1 ESLint flat config（`web/eslint.config.js`）

骨架：
```js
import js from '@eslint/js';
import globals from 'globals';
import tseslint from 'typescript-eslint';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import prettier from 'eslint-config-prettier';

export default tseslint.config(
  { ignores: ['dist', 'node_modules', '.husky', 'vite.config.ts'] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
    },
    settings: { react: { version: 'detect' } },
    plugins: {
      react,
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...react.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      'react/react-in-jsx-scope': 'off',     // Vite + new JSX transform
      'react/jsx-uses-react': 'off',
      'react/prop-types': 'off',              // 用 TS，不用 PropTypes
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
    },
  },
  prettier, // ← 必须放最后：关闭与 Prettier 冲突的格式规则
);
```

**要点**
- `tseslint.config()` 是 v8 的类型安全工厂
- 把 `prettier` 放数组最后，确保覆盖任何冲突的格式规则
- `react-refresh/only-export-components` 只警告，不报错（开发体验）

### 4.2 Prettier（`web/.prettierrc.json`）

```json
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 100,
  "tabWidth": 2,
  "arrowParens": "always"
}
```
与现有源码风格对齐（`web/src/` 已是 single quote + 100 列 + 末尾逗号）。

`web/.prettierignore`:
```
node_modules
dist
.vite
.husky
pnpm-lock.yaml
```

### 4.3 Husky v9（hook 模板 + prepare 脚本）

仓库里只放 `web/scripts/husky-pre-commit.sh`（普通文件，可 review）：
```sh
#!/usr/bin/env sh
pnpm lint-staged
```

`web/package.json` 的 `prepare` 脚本会在 `pnpm install` 后做三件事：
```
husky                                                  # 创建 .husky/_/ + 设 git core.hooksPath
cp scripts/husky-pre-commit.sh .husky/pre-commit       # 把模板装进去
chmod +x .husky/pre-commit                             # 标记可执行
```
husky v9 不再需要 hook 文件里写 `#!/usr/bin/env sh` 头，但我们保留它，使 hook 在不通过 husky 直接执行时也能跑。

### 4.4 lint-staged（写在 `web/package.json`）

```json
"lint-staged": {
  "*.{ts,tsx}":            ["eslint --fix", "prettier --write"],
  "*.{js,json,css,md,html}": ["prettier --write"]
}
```
注意顺序：先 `eslint --fix`（可能改代码），再 `prettier --write`（统一格式），避免 ESLint 自动修复破坏 Prettier 格式。

### 4.5 package.json scripts（变更对比）

**移除**
- `"lint": "tsc --noEmit"`（语义不对，类型检查不是 lint）

**新增/调整**
```json
"scripts": {
  "dev":          "vite",
  "build":        "tsc -b && vite build",
  "preview":      "vite preview",
  "typecheck":    "tsc --noEmit",
  "lint":         "eslint .",
  "lint:fix":     "eslint . --fix",
  "format":       "prettier --write .",
  "format:check": "prettier --check .",
  "prepare":      "husky && cp scripts/husky-pre-commit.sh .husky/pre-commit && chmod +x .husky/pre-commit"
}
```
`prepare` 是 npm/pnpm 在 install 后自动跑的生命周期钩子；husky v9 的 `husky` 命令会在当前目录创建 `.husky/_/` 并执行 `git config core.hooksPath .husky`（相对 git root）。在 `web/` 下跑就会把 hook 路径指向 `web/.husky`。

### 4.6 新增 devDependencies

```
eslint@^9
@eslint/js@^9
typescript-eslint@^8
eslint-plugin-react@^7
eslint-plugin-react-hooks@^5
eslint-plugin-react-refresh@^0.4
globals@^15
prettier@^3
eslint-config-prettier@^9
husky@^9
lint-staged@^15
```

---

## 5. Git 仓库前提

Husky 必须在 git 仓库内才能挂 hook。当前项目根**不是** git 仓库（Stage 01 探查记录）。实施步骤会在根目录 `git init`；如果用户已有 git 仓库，跳过即可。

为避免提交 `.env`、`node_modules` 等，根 `.gitignore` 已在 Stage 01 落地，agent / web 各自 `.gitignore` 也已就位。

---

## 6. 扩展点

| 工具 | 当前 | 未来扩展 |
|---|---|---|
| ESLint 规则 | typescript-eslint + react 三件套 + prettier | 加 `import/order`、`unused-imports`、`tailwindcss` 插件等 |
| Husky hooks | 只有 pre-commit | 加 `commit-msg`（commitlint）、`pre-push`（typecheck/test）按需 |
| Prettier | 默认 plugin | 加 `prettier-plugin-tailwindcss` 自动排序 Tailwind class |
| lint-staged | ts/tsx + 杂项 | 后端 Python 加进来时复用同一 husky，glob 加 `*.py` |

---

## 7. 实施步骤

### 已通过 Write/Edit 工具落地

1. ✅ 写 `web/eslint.config.js`
2. ✅ 写 `web/.prettierrc.json` + `web/.prettierignore`
3. ✅ 写 `web/scripts/husky-pre-commit.sh`
4. ✅ 改 `web/package.json`（scripts + lint-staged + devDependencies + prepare）
5. ✅ 改 `web/.gitignore`（加 `.eslintcache`）
6. ✅ 更新 `web/README.md`、`docs/README.md`、本文档

### 待在 shell 执行（Bash classifier 当前阻塞 git/pnpm 命令）

```bash
# 1) 项目根 git init（husky 必需）
cd /Users/angelo/Desktop/AI/basic-agent
git init

# 2) web/ 装依赖，prepare 脚本自动安置 husky hook
cd web
pnpm install

# 3) 全仓格式化 + lint 修复（让现有代码符合新规则）
pnpm format
pnpm lint --fix

# 4) 提交验证（可选）
cd /Users/angelo/Desktop/AI/basic-agent
git add .
git commit -m "stage 02: frontend tooling"
```

---

## 8. 验证方式

```bash
cd /Users/angelo/Desktop/AI/basic-agent/web

# 8.1 单跑 lint / format
pnpm lint               # 应无错误
pnpm format:check       # 应通过

# 8.2 hook 触发验证
git add .
git commit -m "stage 02: tooling"   # → lint-staged 跑，eslint+prettier 自动作用于改动文件
git log -1              # 应看到 commit

# 8.3 故意制造问题验证
echo "const x:string='no-semicolon'" >> src/test-bad.ts
git add src/test-bad.ts
git commit -m "bad"     # → lint-staged 自动 fix 引号/分号；若有 lint error，commit 失败
rm src/test-bad.ts
```

**验证清单**
1. `node_modules/.bin/eslint --version` ≥ 9.x
2. `cat .git/config` 含 `hooksPath = web/.husky`（在根目录）
3. `git config core.hooksPath` → `web/.husky`
4. `.husky/pre-commit` 可执行，内容为 `pnpm lint-staged`
5. 提交一个空格违规文件，应被自动修复并入库
6. 提交一个真正的 lint error（如 `no-unused-vars`），commit 应被阻断

---

## 9. 风险与回滚

| 风险 | 缓解 |
|---|---|
| ESLint v9 flat config 与某些插件不兼容 | 选定的 5 个插件均已官方支持 v9（截至 2026/05） |
| husky 在子目录下 hooksPath 设置失败 | 实施步骤 6 后立即 `git config core.hooksPath` 验证；失败回落到根级 husky |
| Prettier 100 列与已有源码不一致 | 实施步骤 8 一次 `pnpm format` 全仓格式化 |
| 现有代码触发 lint error 阻塞提交 | 实施步骤 9 一次 `pnpm lint --fix`；遗留的 warning 不阻塞 |
| 提交慢 | 不在 hook 内跑 tsc / test；lint-staged 只动改动文件 |

回滚：删除 4 个新增文件 + 还原 `web/package.json` 的 scripts/devDeps/lint-staged 段 + `git config --unset core.hooksPath`。无破坏性 schema/数据变更。

---

## 10. 交付清单

### 静态文件（已就位）
- [x] `web/eslint.config.js`
- [x] `web/.prettierrc.json` + `web/.prettierignore`
- [x] `web/scripts/husky-pre-commit.sh`
- [x] `web/package.json` 更新（scripts / lint-staged / devDependencies / prepare）
- [x] `web/.gitignore` 加 `.eslintcache`
- [x] `web/README.md`、`docs/README.md`、本文档

### 用户在 shell 中验证
- [ ] `git init` 在项目根
- [ ] `pnpm install` 触发 husky 安装 + cp hook
- [ ] `pnpm lint` 通过
- [ ] `pnpm format:check` 通过
- [ ] 真实 commit 触发 pre-commit hook
