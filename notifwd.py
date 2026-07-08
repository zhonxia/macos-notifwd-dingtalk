#!/usr/bin/env python3
# notifwd for macOS — DingTalk edition
# Based on notifwd by Jordan Mann
# https://github.com/jrmann100/notifwd
# Modified to forward to DingTalk instead of Prowl

__version__ = "0.6-dingtalk"

import subprocess, sqlite3
from datetime import datetime
import plistlib
import sched, time
import requests
from sys import argv, maxsize, stdout
import argparse
from os import environ, path as os_path
from itertools import cycle
import hmac, hashlib, base64
from collections import deque

# I have been writing a lot of Java and am probably not supposed to
# put everything into one class like this.
class Notification:

    @staticmethod
    def setup(argv):
        parser = argparse.ArgumentParser(
            description="notifwd v%s - macOS notification forwarder (DingTalk)" % __version__,
            prog="notifwd")
        parser.add_argument("--webhook", "-w",
                            help="DingTalk robot webhook URL",
                            default=environ.get("DINGTALK_WEBHOOK"))
        parser.add_argument("--secret", "-s",
                            help="DingTalk robot secret (for HMAC signing)",
                            default=environ.get("DINGTALK_SECRET"))
        parser.add_argument("--frequency", "-f", type=int,
                          help="Frequency, in seconds, to check for new notifications.",
                          default=5)
        parser.add_argument("--version", action="store_true",
                            help="Get program version")
        parser.add_argument("--silent", action="store_true",
                            help="Don't display the splash screen or verbose logging.")
        parser.add_argument("--test", "-t",
                            help="Display a test notification on startup.", action="store_true")
        args = parser.parse_args()
        if args.version:
            print("notifwd v%s" % __version__)
            raise SystemExit()
        if args.webhook is None:
            parser.error("no webhook URL specified. Is $DINGTALK_WEBHOOK defined?")
        if args.frequency <= 0:
            parser.error("frequency must be a positive integer.")
        Notification.WEBHOOK = args.webhook
        Notification.SECRET = args.secret or ""
        Notification.FREQ = args.frequency
        Notification.SILENT = args.silent
        Notification.TEST = args.test
        # Rate limiting: DingTalk allows 20 msg/min, we use 18 to be safe
        Notification._ratelimit = deque(maxlen=18)
        if not Notification.SILENT: print(r"""
  _   _       _   _ _____             _
 | \ | | ___ | |_(_)  ___|_       ___| |
 |  \| |/ _ \| __| | |_  \ \ /\ / / _` |
 | |\  | (_) | |_| |  _|   V  V / (_| |
 |_| \_|\___/ \__|_|_|     \_/\_/ \__,_|

notifwd by Jordan Mann (DingTalk edition). Starting up... """, end="")
        # Try DARWIN_USER_DIR first (older macOS), fall back to Group Containers (newer macOS)
        tmp_path = subprocess.run(["getconf", "DARWIN_USER_DIR"], stdout=subprocess.PIPE).stdout
        db_path = tmp_path.decode("utf-8").rstrip() + "com.apple.NotificationCenter/db2/db"
        db_stat = subprocess.run(["stat", db_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
        if db_stat:
            db_path = tmp_path.decode("utf-8").rstrip() + "com.apple.notificationcenter/db2/db"
            db_stat = subprocess.run(["stat", db_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
        if db_stat:
            db_path = os_path.expanduser("~/Library/Group Containers/group.com.apple.usernoted/db2/db")
        Notification.connection = sqlite3.connect(db_path)
        Notification.cursor = Notification.connection.cursor()
        # Set the most recent notification ID to the ID of the last-displayed notification.
        last_data = Notification.get_notification_data(0)
        if last_data:
            Notification.last_id = last_data[0]
            Notification.last_date = last_data[6]
        if Notification.TEST:
            print("Sending test notification... ", end="")
            subprocess.run(["osascript", "-e", "display notification time string of (current date) with title \"The time is\" subtitle \"Most definitely\""])
        if not Notification.SILENT: print("done.")

    @staticmethod
    def main(argv):
        Notification.setup(argv)
        s = sched.scheduler(time.time, time.sleep)
        #https://stackoverflow.com/a/22616059/9068081
        spinner = cycle(['*','-', '/', '|', '\\','-','*'])
        def scheduled_update(s):
            if not Notification.SILENT:
                for i in range(0,7):
                    time.sleep(0.1)
                    stdout.write(next(spinner))
                    stdout.flush()
                    stdout.write('\b')

            Notification.check()
            # Schedule to run periodically.
            s.enter(Notification.FREQ - 0.7, 1, scheduled_update, (s,))
        # Schedule to run on start.
        s.enter(0, 1, scheduled_update, (s,))
        try:
            print("Starting scheduler. Update frequency is %d second%s. " % (Notification.FREQ, ("s" if Notification.FREQ != 1 else "")), end="")
            stdout.flush()
            s.run()
        except KeyboardInterrupt:
            print("\nQuitting...")
            Notification.connection.close()
            raise SystemExit
        except Exception as e:
            raise(e)

    # Create current Cocoa Core Data Timestamp (seconds since Jan 1 2001)
    # and subtract notification date to find how many seconds ago it was.
    # https://www.epochconverter.com/coredata
    @staticmethod
    def coredata_now():
        return (datetime.utcnow() - datetime(2001,1,1)).total_seconds()

    # Fetch data for a specific notification from the database.
    @staticmethod
    def get_notification_data(n):
        return Notification.cursor.execute("SELECT * FROM (SELECT * FROM record ORDER BY rec_id DESC LIMIT %d) ORDER BY rec_id LIMIT 1" % (n + 1)).fetchone()

    # Get an application name like "Messages" from an identifier like "com.apple.Messages"
    # that comes with the notification.
    @staticmethod
    def lookup_display_name(identifier):
        try:
            return subprocess.run(["mdfind", "kMDItemCFBundleIdentifier", "=",
                                   identifier.strip(), "-attr", "kMDItemDisplayName"],
                                  stdout=subprocess.PIPE).stdout.decode("utf-8").split(" = ")[-1].strip()
        except:
            return identifier.split(".")[-1]

    @staticmethod
    def _sign(secret, timestamp):
        sign_string = "%s\n%s" % (timestamp, secret)
        signature = hmac.new(secret.encode(), sign_string.encode(), hashlib.sha256).digest()
        return base64.b64encode(signature).decode()

    @staticmethod
    def _wait_ratelimit():
        now = time.time()
        q = Notification._ratelimit
        while q and q[0] < now - 60:
            q.popleft()
        if len(q) >= 18:
            sleep_time = q[0] + 60 - now
            if sleep_time > 0:
                if not Notification.SILENT:
                    print("\nRate limited, sleeping %.1fs" % sleep_time)
                time.sleep(sleep_time)
            q.popleft()
        q.append(time.time())

    # Initialize nonstatic Notification attributes.
    def __init__(self):
        self.identifier = ""
        self.app = ""
        self.title = ""
        self.subtitle = ""
        self.body = ""
        # Combined body and subtitle.
        self.text = ""
        self.ago = 0
        self.date = 0
        self.xml = ""

    # Display notification info, for logging.
    def __str__(self):
        return ("%d minutes ago from %s: \"%s\"" % (
            int(self.ago/60), self.app, self.title.strip()))

    # Collect recent notifications.
    @staticmethod
    def check():
        # Cross-check by timestamps, so dismissed notifications don't break tracking.
        n = 0
        sql_data = Notification.get_notification_data(n)
        if sql_data:
            newest_id = sql_data[0]
            newest_date = (sql_data[6] if sql_data[6] != None else sql_data[4])
            while sql_data[0] != Notification.last_id and (sql_data[6] if sql_data[6] != None else sql_data[4]) >= Notification.last_date:
                Notification.send(Notification.parse_notification(sql_data[3]))
                n += 1
                sql_data = Notification.get_notification_data(n)
            Notification.last_id = newest_id
            Notification.last_date = newest_date

    # Create a notification from raw plist data. The returned notification can then be sent.
    @staticmethod
    def parse_notification(raw_plist):
        this = Notification()
        data = plistlib.loads(raw_plist)
        for key, value in data.items():
            if key == "app":
                this.identifier = value or ""
                this.app = Notification.lookup_display_name(value) or ""
            elif key == "date":
                this.date = float(value)
                this.ago = Notification.coredata_now() - float(value)
            elif key == "req":
                for subkey, subvalue in value.items():
                    if subkey == "titl":
                        this.title = subvalue or ""
                    if subkey == "subt":
                        this.subtitle = subvalue or ""
                    if subkey == "body":
                        this.body = subvalue or ""
        # Merge subtitle and body — notifications have three lines.
        this.text = this.subtitle + ("\u2014" if this.subtitle else "") + this.body
        return this

    # Send a notification to DingTalk.
    def send(self):
        Notification._wait_ratelimit()
        if not Notification.SILENT:
            print("\nSending notification from", self)
        # Build markdown message
        parts = [self.body]
        if self.subtitle:
            parts.insert(0, self.subtitle)
        msg_body = "\n".join(parts) if parts else "(empty)"
        markdown = "# %s\n" % self.app
        if self.title:
            markdown += "### %s\n" % self.title
        markdown += msg_body
        payload = {
            "msgtype": "markdown",
            "markdown": {"title": self.app, "text": markdown},
        }
        url = Notification.WEBHOOK
        if Notification.SECRET:
            timestamp = str(round(time.time() * 1000))
            sign = Notification._sign(Notification.SECRET, timestamp)
            url = "%s&timestamp=%s&sign=%s" % (url, timestamp, sign)
        try:
            r = requests.post(url, json=payload, timeout=10)
            result = r.json()
            if result.get("errcode") != 0:
                print("DingTalk error: %s" % result)
            elif not Notification.SILENT:
                print("Sent to DingTalk: %s" % self.app)
        except Exception as e:
            print("DingTalk send error: %s" % e)

if __name__ == "__main__":
    Notification.main(argv)
