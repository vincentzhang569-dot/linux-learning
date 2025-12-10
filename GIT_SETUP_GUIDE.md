# 🚀 GitHub 仓库同步完整指南（零基础版）

## 📋 准备工作

### 第一步：检查是否安装了 Git

1. 按 `Win + R` 键，输入 `cmd`，按回车
2. 在黑色窗口（命令提示符）中输入：
   ```bash
   git --version
   ```
3. 如果显示版本号（如 `git version 2.xx.x`），说明已安装 ✅
4. 如果显示"不是内部或外部命令"，需要先安装 Git：
   - 访问：https://git-scm.com/download/win
   - 下载并安装（全部点"下一步"即可）

---

## 🔧 第二步：配置 Git（首次使用需要）

### 📧 关于邮箱的重要说明

**邮箱的作用**：
- ✅ **不是必须和 GitHub 邮箱完全一致**，但建议一致
- ✅ 主要用于标识你的提交记录（显示在 GitHub 上）
- ✅ 如果邮箱匹配，GitHub 会自动关联你的账户，贡献图会更准确
- ⚠️ **不会影响代码推送**，只是用于记录提交者信息

**你的情况**：
- 你的 GitHub 邮箱：`vincentzhang569@gmail.com`
- **建议使用这个邮箱**，这样提交记录会自动关联到你的 GitHub 账户

### 配置命令

在命令提示符中依次输入以下命令：

```bash
git config --global user.name "vincentzhang569-dot"
git config --global user.email "vincentzhang569@gmail.com"
```

**说明**：
- `user.name`：你的 GitHub 用户名（不是显示名称）
- `user.email`：你的 GitHub 邮箱（建议使用绑定的邮箱）

**如果以后想修改**，重新执行上面的命令即可。

---

## 📁 第三步：进入项目文件夹

在命令提示符中输入：

```bash
cd D:\my-ai-brain
```

---

## 🎯 第四步：初始化 Git 仓库并连接 GitHub

### 4.1 初始化本地 Git 仓库

```bash
git init
```

### 4.2 添加远程仓库地址

```bash
git remote add origin https://github.com/vincentzhang569-dot/my-ai-brain.git
```

### 4.3 检查远程仓库是否添加成功

```bash
git remote -v
```

应该显示：
```
origin  https://github.com/vincentzhang569-dot/my-ai-brain.git (fetch)
origin  https://github.com/vincentzhang569-dot/my-ai-brain.git (push)
```

---

## ⚠️ 第五步：处理远程仓库已有的文件

因为你的 GitHub 仓库里已经有文件了，我们需要先拉取下来，然后合并。

### 5.1 拉取远程仓库内容

```bash
git pull origin main --allow-unrelated-histories
```

**如果出现冲突提示**：
- 不要慌！这是正常的
- 输入 `:wq` 然后按回车（这是退出编辑器）

### 5.2 如果出现网络错误（如 "Could not resolve host"）

**错误原因**：
- 网络连接问题
- DNS 解析失败
- 需要代理（某些地区访问 GitHub 需要）

**解决方案 A：跳过拉取，直接推送（推荐）**

如果远程仓库的文件不重要，或者你想用本地文件覆盖，可以**跳过这一步**，直接进入第六步。

**解决方案 B：检查网络连接**

1. 先测试能否访问 GitHub：
   ```bash
   ping github.com
   ```
   - 如果能 ping 通，继续尝试拉取
   - 如果 ping 不通，检查网络或使用代理

2. 如果使用代理，配置 Git 代理：
   ```bash
   git config --global http.proxy http://127.0.0.1:7897
   git config --global https.proxy http://127.0.0.1:7897
   ```
   （把 `7890` 改成你的代理端口）

3. 如果不需要代理，取消代理设置：
   ```bash
   git config --global --unset http.proxy
   git config --global --unset https.proxy
   ```

**解决方案 C：使用强制推送（会覆盖远程文件）**

如果远程文件不重要，可以跳过拉取，直接推送（见第六步）。

---

## 📦 第六步：添加所有文件到 Git

```bash
git add .
```

这个命令会把当前文件夹下所有文件（除了 .gitignore 里排除的）添加到 Git。

---

## 💾 第七步：提交更改

```bash
git commit -m "重构代码：统一 LLM 客户端管理，添加 core 模块"
```

（`-m` 后面的内容是提交说明，可以改成任何你想要的描述）

---

## 🚀 第八步：推送到 GitHub

### 8.1 第一次推送（设置上游分支）

```bash
git push -u origin main
```

### 8.2 如果提示需要登录

- GitHub 现在需要**个人访问令牌（Personal Access Token）**而不是密码
- 如果提示输入用户名和密码：
  1. 用户名：你的 GitHub 用户名
  2. 密码：**不是你的 GitHub 密码**，而是个人访问令牌

### 8.3 如何创建个人访问令牌

1. 登录 GitHub
2. 点击右上角头像 → **Settings**
3. 左侧菜单最下方 → **Developer settings**
4. 点击 **Personal access tokens** → **Tokens (classic)**
5. 点击 **Generate new token** → **Generate new token (classic)**
6. 填写：
   - Note（备注）：`my-ai-brain`
   - 勾选 `repo`（全部权限）
7. 点击 **Generate token**
8. **复制生成的令牌**（只显示一次！）
9. 在命令提示符输入密码时，粘贴这个令牌

---

## ✅ 第九步：验证是否成功

1. 打开浏览器，访问：https://github.com/vincentzhang569-dot/my-ai-brain
2. 刷新页面
3. 应该能看到所有文件，包括 `core/` 文件夹

---

## 🔄 以后如何更新代码

以后每次修改代码后，只需要执行：

```bash
cd D:\my-ai-brain
git add .
git commit -m "描述你做了什么修改"
git push
```

---

## 📝 关于 Streamlit 的说明

### 如果使用 Streamlit Cloud 部署：

1. **不需要修改任何代码** ✅
2. Streamlit Cloud 会自动从 GitHub 拉取最新代码
3. 你只需要在 Streamlit Cloud 的 Dashboard 中点击 **"Reboot app"** 即可

### 如果使用本地 Streamlit：

1. **不需要修改任何配置** ✅
2. 代码会自动使用本地的 `.streamlit/secrets.toml` 文件
3. 直接运行 `streamlit run main.py` 即可

---

## ❓ 常见问题

### Q1: 提示 "fatal: not a git repository"
**解决**：确保你在 `D:\my-ai-brain` 文件夹下执行命令

### Q2: 提示 "remote origin already exists"
**解决**：执行以下命令删除后重新添加：
```bash
git remote remove origin
git remote add origin https://github.com/vincentzhang569-dot/my-ai-brain.git
```

### Q3: 推送时提示 "Permission denied"
**解决**：检查个人访问令牌是否正确，或者重新生成一个

### Q4: 想放弃所有更改，重新开始
**解决**：
```bash
git reset --hard
git clean -fd
```

---

## 🎉 完成！

现在你的本地文件夹已经和 GitHub 仓库完全同步了！

