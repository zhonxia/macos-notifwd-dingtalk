#!/bin/bash
# notifwd-dingtalk 一键启动
# 双击此文件即可在终端中启动通知转发

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# 加载环境变量（如果有 .env 文件）
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

# 检查必要配置
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

# 确保依赖已安装
pip3 install -q requests 2>/dev/null

echo "================================================"
echo "  notifwd-dingtalk"
echo "  macOS Notification → DingTalk 转发器"
echo "================================================"
echo ""
echo "  关闭此终端窗口即可停止监听"
echo ""

python3 notifwd.py --silent
