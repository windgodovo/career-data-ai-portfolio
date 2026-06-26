# Upload To GitHub Runbook (VS Code + GitHub Desktop)

## 目标

这份文档用于新项目首次上传 GitHub，以及后续日常更新推送。
包含你这次使用过的流程：
- 在 GitHub Desktop 里初始化本地仓库
- 在云端创建仓库并关联
- 用 VS Code 终端完成提交与推送

---

## 一次性准备

1. 安装并登录
- 安装 Git
- 安装 GitHub Desktop
- 在 GitHub Desktop 登录账号

2. 项目根目录确认
- 在 VS Code 打开项目根目录
- 终端进入项目根目录

3. 创建 .gitignore（强烈建议先做）
- 必须忽略：.env、.venv、缓存目录、构建产物、大体积运行数据
- 先执行 git status 检查是否有敏感文件将被提交

---

## 路线 A：先在本地初始化，再发布到 GitHub（推荐）

### A1. VS Code 终端初始化

```bash
git init
git branch -m main
git add .
git commit -m "feat: initial commit"
```

### A2. GitHub Desktop 发布云端仓库

1. 打开 GitHub Desktop
2. File -> Add local repository（添加本地项目）
3. 点击 Publish repository
4. 填写仓库名、可见性（Public/Private）
5. 确认发布

发布成功后，GitHub Desktop 会自动配置 origin 并推送。

---

## 路线 B：先在 GitHub 网页创建仓库，再从本地推送

### B1. 在 GitHub 网页创建空仓库

建议不要勾选初始化 README（可减少无关历史冲突）。

### B2. 本地关联并推送

```bash
git init
git branch -m main
git add .
git commit -m "feat: initial commit"
git remote add origin <YOUR_REPO_URL>
git push -u origin main
```

---

## 如果出现 push 被拒绝（fetch first）

说明远程已有提交（例如远程先有 README）。

1. 拉取并合并历史

```bash
git fetch origin main
git pull origin main --allow-unrelated-histories --no-rebase
```

2. 解决冲突
- 常见冲突文件：.gitignore、README
- 修改后执行：

```bash
git add <conflicted_files>
git commit -m "chore: resolve merge conflict"
```

3. 再推送

```bash
git push -u origin main
```

---

## 日常更新（第二次以后）

```bash
git pull
git status
git add .
git commit -m "feat/fix/docs/chore: message"
git push
```

---

## 常见问题速查

### 1) 不是 Git 仓库

现象：fatal: not a git repository

处理：

```bash
git init
```

### 2) 误提交敏感文件

处理：
1. 立刻补充 .gitignore
2. 用 git rm --cached 从索引移除已跟踪敏感文件
3. 重新提交
4. 若已推送到公网，立即更换密钥

### 3) 分支名不一致

处理：

```bash
git branch -m main
git push -u origin main
```

### 4) 认证失败

处理：
- 优先在 GitHub Desktop 重新登录
- 或在命令行使用 PAT（个人访问令牌）

---

## 本项目推荐提交前检查

```bash
git status
git remote -v
git branch --show-current
```

确认：
- 当前分支是 main
- origin 指向预期仓库
- 无 .env、.venv、data/chroma 实际数据库文件进入暂存区

---

## 命名建议

- 首次提交：feat: initial project scaffold
- 配置修复：chore: update gitignore and project metadata
- 功能开发：feat: ...
- 缺陷修复：fix: ...
- 文档更新：docs: ...
