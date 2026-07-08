#!/bin/bash
# notifwd-dingtalk 关闭程序
# 杀死所有正在运行的 notifwd.py 进程

pkill -f "python3 notifwd.py" 2>/dev/null && echo "已停止 notifwd-dingtalk" || echo "notifwd-dingtalk 未在运行"
