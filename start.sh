#!/bin/bash

# 启动脚本 - 同时启动前端和后端服务
# 作者: Cascade
# 创建日期: 2025-04-15

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    echo -e "${2}[$(date +"%H:%M:%S")] $1${NC}"
}

# 检查端口是否被占用
check_port() {
    if lsof -i :$1 > /dev/null 2>&1; then
        print_message "警告: 端口 $1 已被占用，尝试终止进程..." "${YELLOW}"
        lsof -ti :$1 | xargs kill -9 2>/dev/null
        sleep 1
    fi
}

# 清理函数 - 在脚本退出时终止所有子进程
cleanup() {
    print_message "正在终止所有服务..." "${YELLOW}"
    
    # 终止所有子进程
    if [ ! -z "$API_PID" ]; then
        print_message "终止API服务器 (PID: $API_PID)" "${YELLOW}"
        kill $API_PID 2>/dev/null
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        print_message "终止前端服务器 (PID: $FRONTEND_PID)" "${YELLOW}"
        kill $FRONTEND_PID 2>/dev/null
    fi
    
    print_message "所有服务已终止" "${GREEN}"
    exit 0
}

# 注册清理函数
trap cleanup EXIT INT TERM

# 显示欢迎信息
echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}   趋势内容聚合平台 - 启动脚本     ${NC}"
echo -e "${BLUE}=====================================${NC}"

# 检查端口
print_message "检查端口状态..." "${BLUE}"
check_port 8000
check_port 3000

# 启动API服务器
print_message "启动API服务器..." "${BLUE}"
cd "$(dirname "$0")"
uv run python api_server.py &
API_PID=$!

# 等待API服务器启动
print_message "等待API服务器启动..." "${BLUE}"
sleep 3

# 检查API服务器是否成功启动
if ! lsof -i :8000 > /dev/null 2>&1; then
    print_message "错误: API服务器启动失败" "${RED}"
    exit 1
fi
print_message "API服务器已启动 (PID: $API_PID)" "${GREEN}"

# 启动前端服务器
print_message "启动前端服务器..." "${BLUE}"
cd frontend
npm run dev &
FRONTEND_PID=$!

# 等待前端服务器启动
print_message "等待前端服务器启动..." "${BLUE}"
sleep 5

# 检查前端服务器是否成功启动
if ! lsof -i :3000 > /dev/null 2>&1; then
    print_message "错误: 前端服务器启动失败" "${RED}"
    exit 1
fi
print_message "前端服务器已启动 (PID: $FRONTEND_PID)" "${GREEN}"

# 显示访问信息
echo -e "${BLUE}=====================================${NC}"
print_message "所有服务已成功启动!" "${GREEN}"
print_message "API服务器: http://localhost:8000" "${GREEN}"
print_message "前端应用: http://localhost:3000" "${GREEN}"
print_message "按 Ctrl+C 终止所有服务" "${YELLOW}"
echo -e "${BLUE}=====================================${NC}"

# 保持脚本运行
wait
