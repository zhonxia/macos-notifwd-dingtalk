#!/bin/bash
# notifwd-dingtalk 启动（调试模式，显示日志）
# 双击此文件在终端中启动，会显示实时转发日志

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

if [ -z "$DINGTALK_WEBHOOK" ]; then
    echo "================================================"
    echo "  错误：未配置 DINGTALK_WEBHOOK"
    echo ""
    echo "  请在项目目录创建 .env 文件，内容如下："
    echo "  DINGTALK_WEBHOOK=\"https://oapi.dingtalk.com/robot/send?access_token=xxx\""
    echo "  DINGTALK_SECRET=\"SEC...\"  # 可选，加签模式需要"
    echo "================================================"
    exit 1
fi

pip3 install -q requests 2>/dev/null

echo "================================================"
echo "  notifwd-dingtalk (调试模式)"
echo "  macOS Notification → DingTalk 转发器"
echo "================================================"
echo ""
echo "  关闭此终端窗口即可停止监听"
echo ""

python3 notifwd.py
