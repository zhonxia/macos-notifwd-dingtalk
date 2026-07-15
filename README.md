# notifwd — DingTalk Edition

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Platform](https://img.shields.io/badge/platform-macOS-lightgrey)
![Python](https://img.shields.io/badge/python-3.6+-blue)

[🇨🇳 中文](README.zh.md) | [🇬🇧 English](README.md)

> Forward macOS Notification Center alerts to DingTalk group chat in real time.

A fork of [notifwd](https://github.com/jrmann100/notifwd) by Jordan Mann, with the backend swapped from Prowl to DingTalk Webhook.

---

## How It Works

macOS Notification Center stores all notifications in a SQLite database at `~/Library/Group Containers/group.com.apple.usernoted/db2/db`. This tool periodically polls that database for new notifications, parses them (title, subtitle, body, source app), and forwards them to a DingTalk group via the DingTalk Bot Webhook API in Markdown format.

Supports HMAC-SHA256 signing (DingTalk's "Signature" security mode).

---

## Prerequisites

- macOS (Notification Center database path is macOS-specific)
- Python 3.6+
- `pip install requests`

---

## Quick Start

### 1. Create a DingTalk Bot

Create a custom bot (Webhook) in your target DingTalk group:

1. Group Settings → Smart Group Assistant → Add Bot → Custom
2. Set bot name and configure security (recommend **Signature** mode)
3. Copy the Webhook URL and Secret

### 2. One-Click Launch (Recommended)

The project includes double-clickable scripts:

- **Double-click `start-notifwd.command`** → Opens terminal, starts forwarding (silent mode)
- **Double-click `start-notifwd-debug.command`** → Debug mode, shows live forwarding log
- **Double-click `stop-notifwd.command`** → Stops the running process

Before first use, create a `.env` file (`.env.example` is provided as a template):

```bash
cd /path/to/notifwd-dingtalk
cp .env.example .env
# Edit .env with your Webhook URL and Secret
```

After setup, just double-click `start-notifwd.command` — close the terminal window to stop.

### 3. CLI Usage (Alternative)

```bash
# Via environment variables (recommended)
export DINGTALK_WEBHOOK="https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"
export DINGTALK_SECRET="SEC..."  # If signature mode is enabled
python3 notifwd.py

# Or via command-line arguments
python3 notifwd.py \
  --webhook "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN" \
  --secret "SEC..."
```

### 4. Permissions

macOS requires **Full Disk Access** to read the Notification Center database.

- **Option A**: If running from Terminal → grant **Terminal** (or iTerm2) Full Disk Access
  - System Settings → Privacy & Security → Full Disk Access → Add Terminal
- **Option B**: If running via launchd/auto-start → grant **Python** (or `/usr/bin/python3`) Full Disk Access

---

## CLI Options

| Parameter | Environment Variable | Description | Default |
|-----------|-------------------|-------------|---------|
| `--webhook -w` | `DINGTALK_WEBHOOK` | DingTalk Bot Webhook URL | **Required** |
| `--secret -s` | `DINGTALK_SECRET` | HMAC signing key | Empty (no signing) |
| `--frequency -f` | — | Poll interval (seconds) | `5` |
| `--silent` | — | Silent mode, no log output | `false` |
| `--test -t` | — | Send a test notification on startup | `false` |
| `--version` | — | Show version | — |

---

## Usage Examples

```bash
# Basic: poll every 3 seconds
python3 notifwd.py --webhook "https://oapi.dingtalk.com/robot/send?access_token=xxx" --frequency 3

# Silent mode (suitable for background service)
python3 notifwd.py -w "$DINGTALK_WEBHOOK" -s "$DINGTALK_SECRET" --silent

# Test mode: send a macOS notification to verify connectivity
python3 notifwd.py -w "$DINGTALK_WEBHOOK" -t
```

---

## Running as a Background Service (launchd)

Use macOS launchd to configure it as an auto-start background service.

1. Create plist file `~/Library/LaunchAgents/com.user.notifwd-dingtalk.plist`:

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

2. Load the service:

```bash
launchctl load ~/Library/LaunchAgents/com.user.notifwd-dingtalk.plist
```

---

## Message Format

Messages forwarded to DingTalk use Markdown format:

```markdown
# App Name
### Notification Title
Subtitle — Body content
```

Example:

```markdown
# Messages
### John Doe
Meeting at 3 PM today — Please confirm
```

---

## Rate Limiting

DingTalk custom bots have a limit of 20 messages per minute. This tool includes a built-in rate limiter (`_ratelimit`) with a safe threshold of **18 messages per minute** — it automatically waits when exceeded to avoid throttling.

---

## File Structure

```
notifwd-dingtalk/
├── notifwd.py                    # Main program (single file)
├── requirements.txt              # Python dependencies
├── .env.example                  # Configuration template
├── start-notifwd.command         # Double-click start (silent mode)
├── start-notifwd-debug.command   # Double-click start (debug mode)
├── stop-notifwd.command          # Double-click stop
├── README.md                     # This document (English)
└── README.zh.md                  # Chinese documentation
```

---

## Acknowledgments

- [notifwd](https://github.com/jrmann100/notifwd) by Jordan Mann — the original macOS notification forwarder

---

## License

Based on the original project's MIT License.
