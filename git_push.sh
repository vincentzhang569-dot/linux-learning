#!/bin/bash
# 快速提交并推送到 GitHub 的便捷脚本

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}📦 准备提交更改到 GitHub...${NC}"

# 检查是否有未提交的更改
if [ -z "$(git status --porcelain)" ]; then
    echo -e "${GREEN}✅ 没有需要提交的更改${NC}"
    exit 0
fi

# 显示更改状态
echo -e "${YELLOW}更改的文件：${NC}"
git status --short

# 添加所有更改
echo -e "\n${YELLOW}📝 添加所有更改...${NC}"
git add .

# 提交（如果没有提供提交信息，使用默认信息）
if [ -z "$1" ]; then
    COMMIT_MSG="chore: 更新代码"
else
    COMMIT_MSG="$1"
fi

echo -e "${YELLOW}💾 提交更改: $COMMIT_MSG${NC}"
git commit -m "$COMMIT_MSG"

# 获取当前分支
BRANCH=$(git rev-parse --abbrev-ref HEAD)

# 推送到 GitHub
echo -e "\n${YELLOW}🚀 推送到 GitHub (分支: $BRANCH)...${NC}"
git push origin "$BRANCH"

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ 成功推送到 GitHub！${NC}"
else
    echo -e "\n${RED}❌ 推送失败，请检查网络连接或权限${NC}"
    exit 1
fi


