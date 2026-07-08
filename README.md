# notifwd — DingTalk Edition

> macOS Notification Center → DingTalk 机器人转发器

将 macOS 桌面通知实时转发到钉钉群聊机器人。基于 [notifwd](https://github.com/jrmann100/notifwd) by Jordan Mann 改造，后端从 Prowl 替换为钉钉 Webhook。

## 工作原理

macOS 的通知中心会将所有通知写入 SQLite 数据库 `~/Library/Group Containers/group.com.apple.usernoted/db2/db`。本工具定期轮询该数据库，检测新增通知记录，解析通知内容（标题、副标题、正文、来源 App），通过钉钉机器人 Webhook API 以 Markdown 消息格式转发到指定群聊。

支持 HMAC-SHA256 签名模式（钉钉安全设置中的「加签」方式）。

## 前置条件

- macOS（读取通知中心数据库需要 macOS 特有文件路径）
- Python 3.6+
- `pip install requests`

## 快速开始

### 1. 创建钉钉机器人

在目标钉钉群中创建自定义机器人（Webhook 方式）：

1. 群设置 → 智能群助手 → 添加机器人 → 自定义
2. 填写机器人名称，配置安全设置（推荐使用**加签**模式）
3. 复制 Webhook URL 和 Secret

### 2. 一键启动（推荐）

项目内置了可直接双击运行的启动脚本：

- **双击 `start-notifwd.command`** → 自动弹出终端，开始监听转发（静默模式）
- **双击 `start-notifwd-debug.command`** → 调试模式，显示实时转发日志
- **双击 `stop-notifwd.command`** → 停止正在运行的程序

首次使用前，在项目目录创建 `.env` 配置文件（已提供 `.env.example` 模板）：

```bash
cd /path/to/notifwd-dingtalk
cp .env.example .env
# 然后编辑 .env 填入你的 Webhook URL 和 Secret
```

配置好后，以后直接双击 `start-notifwd.command` 就行，关闭终端窗口即停止监听。

### 3. 命令行运行（可选）

```bash
# 通过环境变量配置（推荐）
export DINGTALK_WEBHOOK="https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"
export DINGTALK_SECRET="SEC..."  # 如果启用了加签
python3 notifwd.py

# 或通过命令行参数
python3 notifwd.py \
  --webhook "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN" \
  --secret "SEC..."
```

### 4. 权限设置

macOS 需要**完整磁盘访问权限 (Full Disk Access)** 才能读取通知中心数据库。

- **方式 A**：如果通过终端运行 → 给 **Terminal**（或 iTerm2）授予完整磁盘访问权限
  - 系统设置 → 隐私与安全性 → 完整磁盘访问权限 → 添加终端应用
- **方式 B**：如果通过 launchd/开机启动运行 → 给 **Python**（或 `/usr/bin/python3`）授予完整磁盘访问权限

## 命令行选项

| 参数 | 环境变量 | 说明 | 默认值 |
|------|---------|------|--------|
| `--webhook -w` | `DINGTALK_WEBHOOK` | 钉钉机器人 Webhook URL | **必填** |
| `--secret -s` | `DINGTALK_SECRET` | HMAC 加签密钥 | 空（不签名） |
| `--frequency -f` | — | 轮询间隔（秒） | `5` |
| `--silent` | — | 静默模式，不输出日志和动画 | `false` |
| `--test -t` | — | 启动时发送一条测试通知 | `false` |
| `--version` | — | 显示版本号 | — |

## 使用示例

```bash
# 基础运行：每 3 秒轮询一次
python3 notifwd.py --webhook "https://oapi.dingtalk.com/robot/send?access_token=xxx" --frequency 3

# 静默模式运行（适合作为后台服务）
python3 notifwd.py -w "$DINGTALK_WEBHOOK" -s "$DINGTALK_SECRET" --silent

# 测试模式：启动后触发一条 macOS 通知验证连通性
python3 notifwd.py -w "$DINGTALK_WEBHOOK" -t
```

## 作为后台服务运行（launchd）

可使用 macOS launchd 将其配置为开机自启的后台服务。

1. 创建 plist 文件 `~/Library/LaunchAgents/com.user.notifwd-dingtalk.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.notifwd-dingtalk</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/notifwd.py</string>
        <string>--silent</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>DINGTALK_WEBHOOK</key>
        <string>https://oapi.dingtalk.com/robot/send?access_token=xxx</string>
        <key>DINGTALK_SECRET</key>
        <string>SEC...</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/notifwd-dingtalk.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/notifwd-dingtalk.err</string>
</dict>
</plist>
```

2. 加载服务：

```bash
launchctl load ~/Library/LaunchAgents/com.user.notifwd-dingtalk.plist
```

## 消息格式

转发到钉钉的消息格式为 Markdown：

```
# 应用名称
### 通知标题
副标题—正文内容
```

示例：

```
# Messages
### 张三
今天下午 3 点开会—收到请回复
```

## 钉钉 API 限频

钉钉自定义机器人有每分钟 20 条的消息频率限制。本工具内置了速率限制器（`_ratelimit`），安全阈值设为每分钟 **18 条**，超出后自动等待，避免被限流。

## 文件结构

```
```
notifwd-dingtalk/
├── notifwd.py                    # 主程序（单文件）
├── requirements.txt              # Python 依赖
├── .env.example                  # 配置模板
├── start-notifwd.command         # 双击启动（静默模式）
├── start-notifwd-debug.command   # 双击启动（调试模式）
├── stop-notifwd.command          # 双击停止
└── README.md                     # 本文档
```

## 致谢

- [notifwd](https://github.com/jrmann100/notifwd) by Jordan Mann — 原始 macOS 通知转发工具

## License

基于原项目 MIT License。
