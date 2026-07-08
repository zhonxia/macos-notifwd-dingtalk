# notifwd — DingTalk Edition

macOS Notification Center → DingTalk robot forwarder.

Based on [notifwd](https://github.com/jrmann100/notifwd) by Jordan Mann.

## How it works

Periodically checks macOS Notification Center's SQLite database for new notifications, parses them, and forwards to a DingTalk robot via webhook.

## Prerequisites

- Python 3
- `requests` library (`pip install requests`)

## Setup

1. Create a DingTalk robot in your group chat, get the Webhook URL (and secret if using signed mode).

2. Run:

```bash
export DINGTALK_WEBHOOK="https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"
export DINGTALK_SECRET="SEC..."  # optional
python notifwd.py
```

Or pass args directly:

```bash
python notifwd.py --webhook "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN" --secret "SEC..."
```

## Options

| Arg | Env var | Description |
|---|---|---|
| `--webhook -w` | `DINGTALK_WEBHOOK` | DingTalk robot Webhook URL |
| `--secret -s` | `DINGTALK_SECRET` | HMAC signing secret (optional) |
| `--frequency -f` | — | Poll interval in seconds (default: 60) |
| `--silent` | — | Suppress verbose output and spinner |
| `--test -t` | — | Trigger a test macOS notification on startup |
| `--version` | — | Show version |

## Full Disk Access

macOS requires **Full Disk Access** to read the Notification Center database.
Grant it to the app running this script (Terminal, iTerm2, or Python).
